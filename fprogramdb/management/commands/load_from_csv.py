# -*- coding: utf-8 -*-
from __future__ import print_function

import datetime
import os
import posixpath

import sys
import urllib2

import csv
import urlparse

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.db import transaction

from fprogramdb.models import Project, Call, Topic, Programme, Partner, PartnerProject, SourceFile

reload(sys)
sys.setdefaultencoding('utf-8')


sourceurls = {
    'H2020': {
        'organizations': ["http://cordis.europa.eu/data/cordis-h2020organizations.csv",
                          "http://data.europa.eu/euodp/en/data/dataset/cordisH2020projects.rdf"],
        'projects': ["http://cordis.europa.eu/data/cordis-h2020projects.csv",
                     "http://data.europa.eu/euodp/en/data/dataset/cordisH2020projects.rdf"],
        'programmes': ['http://cordis.europa.eu/data/reference/cordisref-H2020programmes.csv',
                       "http://data.europa.eu/euodp/en/data/dataset/cordisref-data.rdf"],
        'topics': ['http://cordis.europa.eu/data/reference/cordisref-H2020topics.csv',
                   "http://data.europa.eu/euodp/en/data/dataset/cordisref-data.rdf"],
    },
    'FP7': {
        'organizations': ["http://cordis.europa.eu/data/cordis-fp7organizations.csv",
                          "http://data.europa.eu/euodp/en/data/dataset/cordisfp7projects.rdf"],
        'projects': ["http://cordis.europa.eu/data/cordis-fp7projects.csv",
                     "http://data.europa.eu/euodp/en/data/dataset/cordisfp7projects.rdf"],
        'programmes': ['http://cordis.europa.eu/data/reference/cordisref-FP7programmes.csv',
                       "http://data.europa.eu/euodp/en/data/dataset/cordisref-data.rdf"],
        'topics': ['http://cordis.europa.eu/data/reference/cordisref-FP7topics.csv',
                   "http://data.europa.eu/euodp/en/data/dataset/cordisref-data.rdf"],
    },
    'FP6': {
        'programmes': ['http://cordis.europa.eu/data/reference/cordisref-FP6programmes.csv',
                       "http://data.europa.eu/euodp/en/data/dataset/cordisref-data.rdf"],
        'organizations': ["http://cordis.europa.eu/data/cordis-fp6organizations.csv",
                          "http://data.europa.eu/euodp/en/data/dataset/cordisfp6projects.rdf"],
        'projects': [
            "http://cordis.europa.eu/data/cordis-fp6projects.csv",
            "http://data.europa.eu/euodp/en/data/dataset/cordisfp6projects.rdf"],
    },
}

if settings.FPROGRAMDB_DIR:
    xml_dir = settings.FPROGRAMDB_DIR
else:
    xml_dir = settings.STATICFILES_DIRS[0]
# TODO handle script output with django loggers


def get_filename_from_uri(uri):
    return posixpath.basename(
            urlparse.urlsplit("http://data.europa.eu/euodp/en/data/dataset/cordisfp6projects.rdf").path
        )


def download_file(uri, filename):
    try:
        csv_urlfile = urllib2.urlopen(uri)
        with open(os.path.join(xml_dir, filename), 'wb') as csvfile:
            csvfile.write(csv_urlfile.read())
        print('{file} downloaded'.format(file=filename))
    except urllib2.HTTPError:
        print('{file} not found'.format(file=filename))


def check_updates(rdf_url, file_uri_to_check=''):
    import rdflib
    from rdflib.namespace import DCTERMS

    graph = rdflib.Graph()
    graph.load(rdf_url)
    _res = {}
    # search for nodes that hold accessURLs (i.e. resources)
    for trip in graph.triples((None, rdflib.term.URIRef(u'http://www.w3.org/ns/dcat#accessURL'), None)):  # ]]
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
    def programmes_to_objects(self, fp='H2020'):

        # because headers change with the programme
        programmes_headers = {
            'H2020': {
                'rcn': 'rcn',
                'code': 'code',
                'title': 'title',
                'shortTitle': 'shortTitle',
                'language': 'language',
            },
            'FP7': {
                'rcn': '\xef\xbb\xbfRCN',
                'code': 'Code',
                'title': 'Title',
                'shortTitle': 'ShortTitle',
                'language': 'Language',
            },
            'FP6': {
                'rcn': '\xef\xbb\xbf"rcn"',
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
                    }
                )
                _new += 1 if created else 0
        print('{fp} - {new} programmes created'.format(
            fp=fp, new=_new))

    def topics_to_objects(self, fp='H2020'):
        _new = 0
        for index, topic in enumerate(self.fp_data['topics']):
            print('{fp} - topic {index}/{len}'.format(
                fp=fp,
                index=index, len=len(self.fp_data['topics'])),
                end='\r'
            )
            topic, created = Topic.objects.update_or_create(
                rcn=topic['topicRcn'],
                defaults={
                    'fp': fp,
                    'code': topic['topicCode'],
                    'title': topic['title'],
                    'legalBasisRcn': topic['legalBasisRcn'],
                    'legalBasisCode': topic['legalBasisCode'],
                }
            )
            _new += 1 if created else 0
        print('{fp} - {new} topics created'.format(
            fp=fp, new=_new))

    def projects_to_objects(self, fp='H2020'):
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

            rcn = project['\xef\xbb\xbfrcn']

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
                defaults={'fundingScheme': project['fundingScheme'], 'fp': fp}
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
                    'topic': topic
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
                    _programme.save()
                    project_ob.programme.add(_programme)
                    project_ob.save()
        print('{fp} - {new} projects created'.format(
            fp=fp, new=_new))

    def organization_dict_to_object(self, pic, project_partner, fp_organization_headers):
        """
        translation of a row of CORDIS organizations file into an object of the db. It tries to override db 
        inconsistencies like missing PICs or different data for each project. 
        
        It is not guaranteed to correctly join all (problematic) entries referring to the same Partner, but it is 
        consistent within multiple runs
                
        the algorithm roughly is:
            if pic is not null: 
                checks whether there already is a Partner with the same legalName but without pic:
                    if present, modifies that entry with the present data
                    otherwise, update_or_creates an entry with that pic
            if pic is null:
                checks whether there already is a Partner with the same (shortName or legalName) and country:
                    if present, returns that entry
                    otherwise, creates a new entry with data present, and pic as empty string
         
        :param pic: project pic
        :param project_partner: dictionary with data from a CORDIS row
        :param fp_organization_headers: header of the CORDIS file
        :return: partner object, bool True if newly created (just for stat)
        """
        created = False
        if pic != '':
            # most common case
            try:
                # some orgs. appear without a pic, but we first search for occurrences in already in db
                # in H2020 db no partner has a blank legalName, so we use that
                partner_ob = Partner.objects.get(
                    legalName=project_partner[fp_organization_headers['name']],
                    pic='',
                )
                for key, value in {
                    'pic': pic,
                    'organizationActivityType': project_partner[fp_organization_headers['activityType']],
                    # 'legalName': project_partner[fp_organization_headers['name']],

                    'postalCode': project_partner[fp_organization_headers['postCode']],
                    'city': project_partner[fp_organization_headers['city']],
                    'street': project_partner[fp_organization_headers['street']],
                    'country': project_partner[fp_organization_headers['country']]
                }.items():
                    setattr(partner_ob, key, value)
                partner_ob.save()
            except Partner.DoesNotExist:
                partner_ob, created = Partner.objects.update_or_create(
                    pic=pic,
                    defaults={
                        'organizationActivityType': project_partner[fp_organization_headers['activityType']],
                        'legalName': project_partner[fp_organization_headers['name']],
                        'shortName': str(project_partner[fp_organization_headers['shortName']]),

                        'postalCode': project_partner[fp_organization_headers['postCode']],
                        'city': project_partner[fp_organization_headers['city']],
                        'street': project_partner[fp_organization_headers['street']],
                        'country': project_partner[fp_organization_headers['country']],
                    }
                )
        elif pic == '':
            try:
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
                for key, value in {
                    'organizationActivityType': project_partner[fp_organization_headers['activityType']],
                    'legalName': project_partner[fp_organization_headers['name']],
                    'shortName': project_partner[fp_organization_headers['shortName']],

                    'postalCode': project_partner[fp_organization_headers['postCode']],
                    'city': project_partner[fp_organization_headers['city']],
                    'street': project_partner[fp_organization_headers['street']],
                    'country': project_partner[fp_organization_headers['country']],
                }.items():
                    setattr(partner_ob, key, value)
                partner_ob.save()

        return partner_ob, created

    def organization_dict_to_object_beforeh2020(self, pic, project_partner, fp_organization_headers):
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
                partner_ob = Partner.objects.get(pic=pic)

            else:
                raise Partner.DoesNotExist
        except Partner.DoesNotExist:
            try:
                try:
                    partner_ob = Partner.objects.get(
                        legalName=project_partner[fp_organization_headers['name']],
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
                    'country': project_partner[fp_organization_headers['country']]
                }.items():
                    setattr(partner_ob, key, value)
                partner_ob.save()
        return partner_ob, created

    def organizations_to_objects(self, fp='H2020'):
        # because headers change with the programme
        organizations_headers = {
            'H2020': {
                'projectRcn': '\xef\xbb\xbfprojectRcn',
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
                'projectRcn': 'projectRcn',
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
                'projectRcn': '\xef\xbb\xbfprojectRcn',
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
                    organizations_headers['H2020']
                )
            else:
                partner_ob, created = self.organization_dict_to_object_beforeh2020(
                    pic, project_partner, organizations_headers[fp])

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
        print('{fp} - {new} organizations created'.format(
            fp=fp, new=_new))

    def read_csv_lists(self, fp='H2020', use_cached=True, update_only=False):
        """
        read/download files related to fp and stores the results in lists
        :param fp: framework string
        :param use_cached: if to use files already downloaded
        :param update_only: downloads resource if updated online
        """
        for data in ['organizations', 'projects', 'programmes', 'topics']:
            _filename = get_filename_from_uri(sourceurls[fp][data][0])
            update_date = ''
            if update_only:
                update_date = check_updates(
                    rdf_url=sourceurls[fp][data][1],
                    file_uri_to_check=sourceurls[fp][data][0]
                )

            try:
                sourcefile = SourceFile.objects.get(
                    file_url=sourceurls[fp][data][0]
                )
            except SourceFile:
                sourcefile = SourceFile()

                sourcefile.euodp_url = sourceurls[fp][data][1]
                sourcefile.file_url = sourceurls[fp][data][0]
                sourcefile.save()

            if data != 'topics' or (data == 'topics' and fp == 'H2020'):
                if (not use_cached or
                        not os.path.exists(os.path.join(
                            xml_dir,
                            _filename)
                        ) or
                        (update_only and update_date > sourcefile.update_date)
                ):

                    download_file(sourceurls[fp][data][0], _filename)

                    sourcefile.update_date = update_date if update_date else check_updates(
                        rdf_url=sourceurls[fp][data][1],
                        file_uri_to_check=sourceurls[fp][data][0]
                    )
                    sourcefile.save()

                with open(os.path.join(xml_dir, _filename), 'rb') as csvfile:
                    self.fp_data[data] = list(csv.DictReader(csvfile, delimiter=';', quotechar='"'))

    def read_fp(self, fp='H2020', cached=True):
        """
        read all info related to a fp and stores it into the db
        :param fp: framework string
        :param cached: use files already downloaded
        """
        self.fp_data = {
            'organizations': [],
            'projects': [],
            'programmes': [],
            'topics': [],
        }

        self.read_csv_lists(fp, cached)
        with transaction.atomic():
            self.programmes_to_objects(fp)

        with transaction.atomic():
            if fp == 'H2020':
                self.topics_to_objects(fp)
        with transaction.atomic():
            self.projects_to_objects(fp)
        with transaction.atomic():
            self.organizations_to_objects(fp)

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument(
            "-fp", "--frameworkprogrammes", dest="fp", choices=[fp for fp in sourceurls],
            nargs='*', help="FPS to be processed", default=['H2020'])
        parser.add_argument(
            "--cached", dest="cached",
            help="FPS to be processed", default="True")

    def handle(self, *args, **options):
        # TODO check euodp for updated datasets
        if 'fp' in options:
            if 'H2020' in options['fp']:
                self.read_fp('H2020', cached=options['cached'])
                options['fp'].remove('H2020')
            else:
                print('You should load H2020 before other FP')

            for fp in options['fp']:
                self.read_fp(fp, cached=options['cached'])
