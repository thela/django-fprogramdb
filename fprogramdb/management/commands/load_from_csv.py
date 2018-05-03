# -*- coding: utf-8 -*-
from __future__ import print_function

import datetime
import os
import posixpath

import sys

import tokenize

try:
    from urllib.request import urlopen
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen
    from urllib2 import HTTPError
import csv
try:
    from urllib import parse
except ImportError:
    import urlparse as parse

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db import transaction

from fprogramdb.models import Project, Call, Topic, Programme, Partner, PartnerProject, EuodpData, FpData, sourceurls

try:
    from importlib import reload
except ImportError:
    pass
reload(sys)
try:
    sys.setdefaultencoding('utf-8')
except AttributeError:
    pass


if settings.FPROGRAMDB_DIR:
    xml_dir = settings.FPROGRAMDB_DIR
else:
    xml_dir = settings.STATICFILES_DIRS[0]
# TODO handle script output with django loggers


def get_filename_from_uri(uri):
    return posixpath.basename(
            parse.urlsplit(uri).path
        )


def download_file(uri, filename):
    print('download', uri, filename)
    try:
        csv_urlfile = urlopen(uri)
        with open(os.path.join(xml_dir, filename), 'wb') as csvfile:
            csvfile.write(csv_urlfile.read())
        print('{file} downloaded'.format(file=filename))
    except HTTPError:
        print('{file} not found'.format(file=filename))


def check_updates(euodp_data=None, rdf_url=None, file_uri_to_check=None):
    if euodp_data:
        rdf_url = euodp_data.euodp_url
        file_uri_to_check = euodp_data.file_url

    import rdflib
    from rdflib.namespace import DCTERMS

    graph = rdflib.Graph()
    graph.load(rdf_url)
    _res = {}
    # search for nodes that hold accessURLs (i.e. resources)
    for trip in graph.triples((None, rdflib.term.URIRef(u'http://www.w3.org/ns/dcat#accessURL'), None)):
        bnode = trip[0]

        # filter nodes that hold csv resources
        if (
                bnode,
                rdflib.term.URIRef(u'http://data.europa.eu/euodp/ontologies/ec-odp#distributionFormat'),
                rdflib.term.Literal(u'text/csv')) in graph.triples((bnode, None, None)):
            if file_uri_to_check and (
                    bnode,
                    rdflib.term.URIRef(u'http://www.w3.org/ns/dcat#accessURL'),
                    rdflib.term.Literal(file_uri_to_check,
                                        datatype=rdflib.term.URIRef(u'http://www.w3.org/2001/XMLSchema#anyURI'))
            ) in graph.triples((bnode, None, None)):
                return datetime.datetime.strptime(
                    graph.value(bnode, DCTERMS.modified, None)[:19],
                    "%Y-%m-%dT%H:%M:%S") if graph.value(bnode, DCTERMS.modified, None) else datetime.datetime.strptime(
                    graph.value(bnode, DCTERMS.issued, None)[:19], "%Y-%m-%dT%H:%M:%S")
            else:
                # modified
                if graph.value(bnode, DCTERMS.modified, None):
                    _res[
                        str(graph.value(
                            bnode,
                            rdflib.term.URIRef(u'http://www.w3.org/ns/dcat#accessURL'),
                            None))] = datetime.datetime.strptime(
                        graph.value(bnode, DCTERMS.modified, None)[:19],
                        "%Y-%m-%dT%H:%M:%S")
                else:
                    _res[str(graph.value(
                        bnode,
                        rdflib.term.URIRef(u'http://www.w3.org/ns/dcat#accessURL'),
                        None))] = datetime.datetime.strptime(graph.value(bnode, DCTERMS.issued, None)[:19],
                                                             "%Y-%m-%dT%H:%M:%S")
    return _res


class Command(BaseCommand):
    def programmes_to_objects(self, fp='H2020', euodp_data=None):

        for key in self.fp_data['programmes'][0].keys():
            if 'rcn' in key or 'RCN' in key:
                __rcn_key = key

        # because headers change with the programme
        programmes_headers = {
            'H2020': {
                'rcn': __rcn_key,
                'code': 'CODE',
                'title': 'Title',
                'shortTitle': 'ShortTitle',
                'language': 'language',
            },
            'FP7': {
                'rcn': __rcn_key,
                'code': 'Code',
                'title': 'Title',
                'shortTitle': 'ShortTitle',
                'language': 'Language',
            },
            'FP6': {
                'rcn': __rcn_key,
                'code': 'code',
                'title': 'title',
                'shortTitle': 'shortTitle',
                'language': 'language',
            }
        }

        _new = 0
        for index, programme in enumerate(self.fp_data['programmes']):
            print('{fp} - programme {index}/{len}'.format(
                fp=fp,
                index=index, len=len(self.fp_data['programmes'])),
                end='\r'
            )
            if programme[programmes_headers[fp]['language']] == 'en':
                programme, created = Programme.objects.update_or_create(
                    rcn=programme[programmes_headers[fp]['rcn']],
                    defaults={
                        'fp': fp,
                        'code': programme[programmes_headers[fp]['code']],
                        'title': programme[programmes_headers[fp]['title']],
                        'shortTitle': programme[programmes_headers[fp]['shortTitle']],
                        'source': euodp_data,
                    }
                )
                _new += 1 if created else 0
        print('{fp} - {new} programmes created, {index} processed'.format(
            fp=fp, new=_new, index=index+1))

    def topics_to_objects(self, fp='H2020', euodp_data=None):

        # because headers change with the programme
        topics_headers = {
            'H2020': {
                'rcn': 'topicRcn',
                'code': 'topicCode',
                'title': 'title',
                'legalBasisRcn': 'legalBasis',
                'legalBasisCode': 'legalBasisCode',
            },
            'FP7': {
                'rcn': 'topicRcn',
                'code': 'topicCode',
                'title': 'title',
                'legalBasisRcn': 'legalBasisRcn',
                'legalBasisCode': 'legalBasisCode',
            },
            'FP6': {
                'rcn': 'topicRcn',
                'code': 'topicCode',
                'title': 'title',
                'legalBasisRcn': 'legalBasisRcn',
                'legalBasisCode': 'legalBasisCode',
            }
        }
        _new = 0
        for index, topic in enumerate(self.fp_data['topics']):
            print('{fp} - topic {index}/{len}'.format(
                fp=fp,
                index=index, len=len(self.fp_data['topics'])),
                end='\r'
            )

            topic, created = Topic.objects.update_or_create(
                code=topic[topics_headers[fp]['code']],
                defaults={
                    'fp': fp,
                    'rcn': topic[topics_headers[fp]['rcn']],
                    'title': topic[topics_headers[fp]['title']],
                    'legalBasisRcn': topic[topics_headers[fp]['legalBasisRcn']],
                    'legalBasisCode': topic[topics_headers[fp]['legalBasisCode']] if topics_headers[fp]['legalBasisCode'] in topic else '',
                    'source': euodp_data,
                }
            )
            _new += 1 if created else 0
        print('{fp} - {new} topics created, {index} processed'.format(
            fp=fp, new=_new, index=index+1))

    def projects_to_objects(self, fp='H2020', euodp_data=None):
        _new = 0

        for index, project in enumerate(self.fp_data['projects']):
            print('{fp} - project {index}/{len}'.format(
                fp=fp,
                index=index, len=len(self.fp_data['projects'])),
                end='\r'
            )
            try:
                GA = project['id']
            except KeyError:
                GA = project['reference']

            try:
                rcn = project['\xef\xbb\xbfrcn']
            except KeyError:
                rcn = project['\ufeffrcn']

            try:
                start_date = datetime.datetime.strptime(
                    project['startDate'],
                    '%Y-%m-%d')
            except (KeyError, ValueError):
                start_date = None

            try:
                end_date = datetime.datetime.strptime(
                    project['endDate'],
                    '%Y-%m-%d')
            except (KeyError, ValueError):
                end_date = None

            call, created = Call.objects.update_or_create(
                title=project['call'],
                defaults={'fundingScheme': project['fundingScheme'], 'fp': fp, 'source': euodp_data}
            )

            try:
                topic = Topic.objects.get(code=project['topics'])
            except Topic.DoesNotExist:
                topic = None
                print('')
                print('GA {ga} - missing topic: {topics}'.format(
                    ga=GA,
                    topics=project['topics']))
                topic = Topic(code=project['topics'])
                topic.fp = fp
                topic.source = euodp_data
                topic.save()
                print(topic.id)
            try:
                total_cost = float(project['totalCost'].replace(",", "."))
            except ValueError:
                total_cost = 0
            try:
                ecMaxContribution = float(project['ecMaxContribution'].replace(",", "."))
            except ValueError:
                ecMaxContribution = 0

            try:
                UNICODE_EXISTS = bool(type(unicode))
            except NameError:
                unicode = str

            project_ob, created = Project.objects.update_or_create(
                rcn=rcn,
                defaults={
                    'fp': fp,
                    'GA': GA,
                    'acronym': project['acronym'],
                    'title': unicode(project['title']),
                    'objective': unicode(project['objective']),
                    'startDate': start_date,
                    'endDate': end_date,
                    'totalCost': total_cost,
                    'ecMaxContribution': ecMaxContribution,
                    'call': call,
                    'topic': topic,
                    'source': euodp_data,
                }
            )
            _new += 1 if created else 0

            for programme_code in project['programme'].split(';'):
                try:
                    project_ob.programme.add(Programme.objects.get(code=programme_code))
                    project_ob.save()
                except Programme.DoesNotExist:
                    print('')
                    print('GA {ga} - missing programme: {programme_code}'.format(ga=GA, programme_code=programme_code))
                    _programme = Programme(code=programme_code)
                    _programme.fp = fp
                    _programme.source = euodp_data
                    _programme.save()
                    project_ob.programme.add(_programme)
                    project_ob.save()
        print('{fp} - {new} projects created, {index} processed'.format(
            fp=fp, new=_new, index=index+1))

    def organization_dict_to_object(self, pic, project_partner, fp_organization_headers, euodp_data=None):
        """
        translation of a row of CORDIS organizations file into an object of the db. It tries to override db 
        inconsistencies like missing PICs or different data for each project. 
        
        It is not guaranteed to correctly join all (problematic) entries referring to the same Partner, but it is 
        consistent within multiple runs
                
        the algorithm roughly is:
            if pic is not null:
                checks if there is already a Partner with the given pic
            if pic is null:
                checks whether there already is a Partner with the same (shortName or legalName) and country:
                    if present, returns that entry
            otherwise it creates a new partner with the given pic (if-present)

            if the found partner was merged with another, returns the latter

            checks whether there already is a Partner with the same legalName but without pic:
                if present, modifies that entry with the present data
            then all data is updated with the new info

        :param pic: project pic
        :param project_partner: dictionary with data from a CORDIS row
        :param fp_organization_headers: header of the CORDIS file
        :return: partner object, bool True if newly created (just for stat)
        """
        created = False
        try:
            if pic != '':
                '''
                this is a "rewrite" of an update_or_create with the merged check embedded into it
                partner_ob, created = Partner.objects.update_or_create(
                    pic=pic,
                    merged=False,
                    defaults={...}
                )'''
                partner_ob = Partner.objects.get(
                    pic=pic
                )

            elif pic == '':
                _query = Q()
                if project_partner[fp_organization_headers['name']] != '':
                    _query |= Q(legalName=project_partner[fp_organization_headers['name']])
                if project_partner[fp_organization_headers['shortName']] != '':
                    _query |= Q(shortName=project_partner[fp_organization_headers['shortName']])
                if project_partner[fp_organization_headers['country']] != '':
                    _query &= Q(country=project_partner[fp_organization_headers['country']])

                print('\n', project_partner, _query, Partner.objects.filter(
                    _query
                ))

                partner_ob = Partner.objects.get(
                    _query
                )
        except Partner.DoesNotExist:
            created = True
            partner_ob = Partner()
            if pic != '':
                partner_ob.pic = pic

        # if the returned partner_ob was merged, get the latter
        if partner_ob.merged:
            partner_ob = Partner.objects.get(
                id=partner_ob.merged_with_id
            )

        for key, value in {
            'organizationActivityType': project_partner[fp_organization_headers['activityType']],
            'legalName': project_partner[fp_organization_headers['name']],
            'shortName': project_partner[fp_organization_headers['shortName']],

            'postalCode': project_partner[fp_organization_headers['postCode']],
            'city': project_partner[fp_organization_headers['city']],
            'street': project_partner[fp_organization_headers['street']],
            'country': project_partner[fp_organization_headers['country']],
            'source': euodp_data,
        }.items():
            setattr(partner_ob, key, value)
        partner_ob.save()

        # merge existing analogous partner objects without pic with this
        analogous = Partner.objects.filter(
            legalName=project_partner[fp_organization_headers['name']],
            country=project_partner[fp_organization_headers['country']],
            pic='', merged=False,
        )
        if analogous:
            partner_ob.merge_with_models(analogous)

        return partner_ob, created

    def organization_dict_to_object_beforeh2020(self, pic, project_partner, fp_organization_headers, euodp_data=None):
        """
        translation of a row of CORDIS organizations file into an object of the db for fps before H2020.
        We try to ensure consistence with current H2020 data, and before H2020 organizations db is very messy.
        When we can, we use the legalName to link to H2020 organizations.

        the algorithm roughly is:
            if pic not empty and Partner already in db:
                return that Partner

            elif there already is a Partner with the same legalName
                if there is only one Partner with the same legalName
                    return that
                if there are multiple, but a single Partner with the same (legalName and country):
                    return that
                if there are still multiple Partners with the same (legalName and country):
                    return the first occurrence
            otherwise
                create new

        :param pic:
        :param project_partner:
        :param fp_organization_headers:
        :return: partner object, bool True if newly created (just for stat)
        """
        created = False
        try:
            if pic != '':
                partner_ob = Partner.objects.get(pic=pic, merged=False)

            else:
                raise Partner.DoesNotExist
        except Partner.DoesNotExist:
            try:
                try:
                    partner_ob = Partner.objects.get(
                        legalName=project_partner[fp_organization_headers['name']]
                    )
                except Partner.MultipleObjectsReturned:
                    # maybe same legalName but different country?
                    try:
                        partner_ob = Partner.objects.get(
                            legalName=project_partner[fp_organization_headers['name']],
                            country=project_partner[fp_organization_headers['country']],
                        )
                    except Partner.MultipleObjectsReturned:
                        # still multiple? I take the first
                        print('\n', project_partner, Partner.objects.filter(
                            legalName=project_partner[fp_organization_headers['name']],
                        ), Partner.objects.filter(
                            legalName=project_partner[fp_organization_headers['name']],
                            country=project_partner[fp_organization_headers['country']],
                        ))
                        partner_ob = Partner.objects.filter(
                            legalName=project_partner[fp_organization_headers['name']],
                            country=project_partner[fp_organization_headers['country']],
                        )[0]
                # if the returned partner_ob was merged, get the latter
                if partner_ob.merged:
                    partner_ob = Partner.objects.get(
                        id=partner_ob.merged_with_id
                    )
            except Partner.DoesNotExist:
                created = True
                partner_ob = Partner()
                for key, value in {
                    'pic': pic,
                    'organizationActivityType': project_partner[fp_organization_headers['activityType']],
                    'legalName': project_partner[fp_organization_headers['name']],
                    'shortName': project_partner[fp_organization_headers['shortName']],

                    'postalCode': project_partner[fp_organization_headers['postCode']],
                    'city': project_partner[fp_organization_headers['city']],
                    'street': project_partner[fp_organization_headers['street']],
                    'country': project_partner[fp_organization_headers['country']],
                    'source': euodp_data,
                }.items():
                    setattr(partner_ob, key, value)
                partner_ob.save()
        return partner_ob, created

    def organizations_to_objects(self, fp='H2020', euodp_data=None):
        # because headers change with the programme

        for key in self.fp_data['organizations'][0].keys():
            if 'Rcn' in key:
                __rcn_key = key
        organizations_headers = {
            'H2020': {
                'projectRcn': __rcn_key,
                'projectID': 'projectID',
                'projectAcronym': 'projectAcronym',
                'role': 'role',
                'id': 'id',
                'name': 'name',
                'shortName': 'shortName',
                'activityType': 'activityType',
                'endOfParticipation': 'endOfParticipation',
                'ecContribution': 'ecContribution',
                'country': 'country',
                'street': 'street',
                'city': 'city',
                'postCode': 'postCode',
                'organizationUrl': 'organizationUrl',
                'contactType': 'contactType',
                'contactTitle': 'contactTitle',
                'contactFirstNames': 'contactFirstNames',
                'contactLastNames': 'contactLastNames',
                'contactFunction': 'contactFunction',
                'contactTelephoneNumber': 'contactTelephoneNumber',
                'contactFaxNumber': 'contactFaxNumber',
                'contactEmail': 'contactEmail',
            },
            'FP7': {
                'projectRcn': __rcn_key,
                'projectID': 'projectReference',
                'projectAcronym': 'projectAcronym',
                'role': 'role',
                'id': 'id',
                'name': 'name',
                'shortName': 'shortName',
                'activityType': 'activityType',
                'endOfParticipation': 'endOfParticipation',
                'ecContribution': 'ecContribution',
                'country': 'country',
                'street': 'street',
                'city': 'city',
                'postCode': 'postCode',
                'organizationUrl': 'organizationUrl',
                'contactType': 'contactType',
                'contactTitle': 'contactTitle',
                'contactFirstNames': 'contactFirstNames',
                'contactLastNames': 'contactLastNames',
                'contactFunction': 'contactFunction',
                'contactTelephoneNumber': 'contactTelephoneNumber',
                'contactFaxNumber': 'contactFaxNumber',
                'contactEmail': 'contactEmail',
            },
            'FP6': {
                'projectRcn': __rcn_key,
                'projectID': 'projectReference',
                'projectAcronym': 'projectAcronym',
                'role': 'role',
                'id': 'id',
                'name': 'name',
                'shortName': 'shortName',
                'activityType': 'activityType',
                'endOfParticipation': 'endOfParticipation',
                'ecContribution': 'ecContribution',
                'country': 'country',
                'street': 'street',
                'city': 'city',
                'postCode': 'postCode',
                'organizationUrl': 'organizationUrl',
                'contactType': 'contactType',
                'contactTitle': 'contactTitle',
                'contactFirstNames': 'contactFirstNames',
                'contactLastNames': 'contactLastNames',
                'contactFunction': 'contactFunction',
                'contactTelephoneNumber': 'contactTelephoneNumber',
                'contactFaxNumber': 'contactFaxNumber',
                'contactEmail': 'contactEmail',
            }
        }

        _new = 0
        # translates one row for each partner in one Partner object and one ParnerProject link
        for index, project_partner in enumerate(self.fp_data['organizations']):
            print('{fp} - organizations {index}/{len}'.format(
                fp=fp,
                index=index, len=len(self.fp_data['organizations'])),
                end='\r'
            )
            pic = project_partner[organizations_headers[fp]['id']]
            # in H2020 (almost) all partners have a pic. in fp7 appears to lead the legalname
            if fp == 'H2020':
                partner_ob, created = self.organization_dict_to_object(
                    pic,
                    project_partner,
                    organizations_headers['H2020'], euodp_data
                )
            else:
                partner_ob, created = self.organization_dict_to_object_beforeh2020(
                    pic, project_partner, organizations_headers[fp], euodp_data)

            try:
                ec_contribution = float(project_partner[organizations_headers[fp]['ecContribution']].replace(',', '.'))
            except ValueError:
                # no contribution, will be 0
                ec_contribution = 0

            project = Project.objects.get(rcn=project_partner[organizations_headers[fp]['projectRcn']])

            partnerproject, created = PartnerProject.objects.update_or_create(
                partner=partner_ob, project=project,
                defaults={
                    'coordinator': project_partner[organizations_headers[fp]['role']] == 'coordinator',
                    'ecContribution': ec_contribution,
                }
            )
            _new += 1 if created else 0
        print('{fp} - {new} organizations created, {index} processed'.format(
            fp=fp, new=_new, index=index+1))

    def read_csv_lists(self, fp, use_cached=True, update_only=False):
        """
        read/download files related to fp and stores the results in lists
        :param fp: framework string
        :param use_cached: if to use files already downloaded
        :param update_only: downloads resource if updated online

        returns the FpData object
        """

        fp_data_ob, fp_created = FpData.objects.get_or_create(fp=fp)
        if fp_created:
            for data in ['organizations', 'projects', 'programmes', 'topics']:
                if sourceurls[fp][data][1]:
                    euodp_data = EuodpData()

                    euodp_data.euodp_url = sourceurls[fp][data][1]
                    euodp_data.file_url = sourceurls[fp][data][0]
                    euodp_data.save()

                    # sets the correct EuodpData object in FpData
                    setattr(fp_data_ob, data, euodp_data)
            fp_data_ob.save()

        for data in ['organizations', 'projects', 'programmes', 'topics']:
            euodp_data = getattr(fp_data_ob, data)
            if euodp_data:
                _filename = get_filename_from_uri(euodp_data.file_url)
                update_date = ''
                if not use_cached or update_only:
                    update_date = check_updates(euodp_data)

                # choose when to download again the csv file
                if (not os.path.exists(os.path.join(
                        xml_dir,
                        _filename)
                )  # no cache to use
                        or not use_cached  # don't use cache
                        or (update_only  # just download updated
                            and (not euodp_data.update_date or
                                 update_date.date() > euodp_data.update_date
                        ))
                ):
                    download_file(sourceurls[fp][data][0], _filename)
                    euodp_data.update_date = update_date if update_date else check_updates(
                        rdf_url=euodp_data.euodp_url,
                        file_uri_to_check=euodp_data.file_url
                    )
                    euodp_data.save()
                elif not euodp_data.update_date:
                    euodp_data.update_date = update_date if update_date else check_updates(
                        rdf_url=euodp_data.euodp_url,
                        file_uri_to_check=euodp_data.file_url
                    )
                    euodp_data.save()
                try:
                    with open(os.path.join(xml_dir, _filename), encoding='utf-8') as csvfile:
                        self.fp_data[data] = list(csv.DictReader(csvfile, delimiter=';', quotechar='"'))
                except UnicodeDecodeError:
                    with open(os.path.join(xml_dir, _filename), encoding='latin-1') as csvfile:
                        self.fp_data[data] = list(csv.DictReader(csvfile, delimiter=';', quotechar='"'))

        return fp_data_ob

    def read_fp(self, fp='H2020', cached=True, update_only=False):
        """
            read all info related to a fp and stores it into the db
            :param update_only:
            :param fp: framework string
            :param cached: use files already downloaded
        """
        self.fp_data = {
            'organizations': [],
            'projects': [],
            'programmes': [],
            'topics': [],
        }

        fp_data_ob = self.read_csv_lists(fp, cached, update_only)

        if not update_only:
            with transaction.atomic():
                self.programmes_to_objects(fp, fp_data_ob.programmes)

            if fp == 'H2020':
                with transaction.atomic():
                    self.topics_to_objects(fp, fp_data_ob.topics)
            with transaction.atomic():
                self.projects_to_objects(fp, fp_data_ob.projects)
            with transaction.atomic():
                self.organizations_to_objects(fp, fp_data_ob.organizations)

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument(
            "-fp", "--frameworkprogrammes", dest="fp", choices=[fp for fp in sourceurls],
            nargs='*', help="FPS to be processed", default=['H2020'])
        parser.add_argument(
            "--checkupdates", dest="update_only",
            help="only check updates on the db", default="False")
        parser.add_argument(
            "--cached", dest="cached",
            help="FPS to be processed", default="True")

    def handle(self, *args, **options):
        if 'fp' in options:
            if 'H2020' in options['fp']:
                self.read_fp('H2020', cached=options['cached'] != 'False', update_only=options['update_only'] == 'True')
                options['fp'].remove('H2020')
            else:
                print('You should load H2020 before other FP')

            for fp in options['fp']:
                self.read_fp(fp, cached=options['cached'] != 'False', update_only=options['update_only'] == 'True')
