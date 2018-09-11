from __future__ import unicode_literals


# not os.path we need posix
import csv
import datetime

import os


from django.core.validators import validate_comma_separated_integer_list
from django.db import models, transaction
from django.db.models import Q
from django.db.models.query import QuerySet
from django.urls import reverse

from django.conf import settings


try:
    from urllib.request import urlopen
    from urllib.error import HTTPError
except ImportError:
    from urllib2 import urlopen
    from urllib2 import HTTPError

import posixpath
try:
    from urllib import parse
except ImportError:
    import urlparse as parse


FP_CODE = (
    (u'FP1', u'FP1'),
    (u'FP2', u'FP2'),
    (u'FP3', u'FP3'),
    (u'FP4', u'FP4'),
    (u'FP5', u'FP5'),
    (u'FP6', u'FP6'),
    (u'FP7', u'FP7'),
    (u'H2020', u'H2020'),
)

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
        'topics': [None, None],
    },
    'FP6': {
        'programmes': ['http://cordis.europa.eu/data/reference/cordisref-FP6programmes.csv',
                       "http://data.europa.eu/euodp/en/data/dataset/cordisref-data.rdf"],
        'organizations': ["http://cordis.europa.eu/data/cordis-fp6organizations.csv",
                          "http://data.europa.eu/euodp/en/data/dataset/cordisfp6projects.rdf"],
        'projects': [
            "http://cordis.europa.eu/data/cordis-fp6projects.csv",
            "http://data.europa.eu/euodp/en/data/dataset/cordisfp6projects.rdf"],
        'topics': [None, None],
    },
}


if settings.FPROGRAMDB_DIR:
    xml_dir = settings.FPROGRAMDB_DIR
else:
    xml_dir = settings.STATICFILES_DIRS[0]


class EuodpDataFileMethods(object):

    def get_filename_from_uri(self):
        return posixpath.splitext(posixpath.basename(
            parse.urlsplit(self.file_url).path
        ))[0]

    def local_file(self, update_date=None):
        if not update_date:
            update_date = self.update_date
        local_filename = '{filename}-{update_date}.csv'.format(
            filename=self.get_filename_from_uri(),
            update_date=self.update_date.strftime("%Y%m%d")
        )
        return os.path.join(xml_dir, local_filename)

    def download_file(self, filename=None):
        if not filename:
            filename = self.local_file()

        if not os.path.exists(filename):
            print('download', self.file_url, filename)
            try:
                csv_urlfile = urlopen(self.file_url)
                with open(filename, 'wb') as csvfile:
                    csvfile.write(csv_urlfile.read())
                print('{file} downloaded'.format(file=filename))
            except HTTPError:
                print('{file} not found'.format(file=filename))
        else:
            print('using', self.file_url, filename)

    def check_updates(self):

        rdf_url = self.euodp_url
        file_uri_to_check = self.file_url

        import rdflib
        from rdflib.namespace import DCTERMS
        import datetime

        graph = rdflib.Graph()
        try:
            graph.load(rdf_url)
        except TypeError:
            raise Exception("The EUROPA server is temporarily unavailable")
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
                        "%Y-%m-%dT%H:%M:%S").date() if graph.value(bnode, DCTERMS.modified, None) else datetime.datetime.strptime(
                        graph.value(bnode, DCTERMS.issued, None)[:19], "%Y-%m-%dT%H:%M:%S").date()

    def update_file(self, use_cached=False, file_exists=False):

        update_date = ''
        if not use_cached:
            update_date = self.check_updates()

        # choose when to download again the csv file
        if (not use_cached  # don't use cache
                or (not self.update_date or
                    update_date.date() > self.update_date
                )
        ):

            self.update_date = update_date if update_date else self.check_updates(
                rdf_url=self.euodp_url,
                file_uri_to_check=self.file_url
            )
            #print(self.update_date)
            self.download_file()
        elif not self.update_date:
            self.update_date = update_date if update_date else self.check_updates(
                rdf_url=self.euodp_url,
                file_uri_to_check=self.file_url
            )


class EuodpDataMethods(object):
    type_to_method = {
        'organizations': 'organizations_to_objects',
        'projects': 'projects_to_objects',
        'programmes': 'programmes_to_objects',
        'topics': 'topics_to_objects'
    }

    headers_translator = {
        'rcn': ['rcn', 'RCN', 'topicRcn', '\ufeffRCN', '\xef\xbb\xbfrcn', '\ufeff"rcn"', '\ufeffrcn', 'projectRcn', '\ufeffprojectRcn'],
        'code': ['CODE', 'topicCode', 'Code', 'code'],
        'title': ['title', 'Title'],
        'shortTitle': ['ShortTitle', 'shortTitle'],
        'language': ['language', 'Language'],
        'legalBasisRcn': ['legalBasisRcn', 'legalBasis'],
        'legalBasisCode': ['legalBasisCode'],
        'projectID': ['projectID', 'projectReference'],
        'projectAcronym': ['projectAcronym'],
        'role': ['role'],
        'id': ['id'],
        'name': ['name'],
        'shortName': ['shortName'],
        'activityType': ['activityType'],
        'endOfParticipation': ['endOfParticipation'],
        'ecContribution': ['ecContribution'],
        'country': ['country'],
        'street': ['street'],
        'city': ['city'],
        'postCode': ['postCode'],
        'organizationUrl': ['organizationUrl'],
        'contactType': ['contactType'],
        'contactTitle': ['contactTitle'],
        'contactFirstNames': ['contactFirstNames'],
        'contactLastNames': ['contactLastNames'],
        'contactFunction': ['contactFunction'],
        'contactTelephoneNumber': ['contactTelephoneNumber'],
        'contactFaxNumber': ['contactFaxNumber'],
        'contactEmail': ['contactEmail'],
        'startDate': ['startDate'],
        'endDate': ['endDate'],
        'GA': ['id', 'reference'],
        'call': ['call'],
        'topics': ['topics'],
        'fundingScheme': ['fundingScheme'],
        'totalCost': ['totalCost'],
        'ecMaxContribution': ['ecMaxContribution'],
        'acronym': ['acronym'],
        'objective': ['objective'],
        'programme': ['programme'],
    }

    def get_headers_translation(self, keys):
        _res = {}
        # gets the key for RCN from known patterns
        for key in keys:
            for header in self.headers_translator:
                if key in self.headers_translator[header]:
                    _res.update({header: key})
        return _res

    def programmes_to_objects(self, fp, csv_list):

        # because headers change with the programme
        programmes_headers = self.get_headers_translation(csv_list[0].keys())

        _new = 0
        for index, programme in enumerate(csv_list):
            print('{fp} - programme {index}/{len}'.format(
                fp=fp,
                index=index, len=len(csv_list)),
                end='\r'
            )
            if programme[programmes_headers['language']] == 'en':
                programme, created = Programme.objects.update_or_create(
                    rcn=programme[programmes_headers['rcn']],
                    defaults={
                        'fp': fp,
                        'code': programme[programmes_headers['code']],
                        'title': programme[programmes_headers['title']],
                        'shortTitle': programme[programmes_headers['shortTitle']],
                        'source': self,
                    }
                )
                _new += 1 if created else 0
        print('{fp} - {new} programmes created, {index} processed'.format(
            fp=fp, new=_new, index=index+1))

    def topics_to_objects(self, fp, csv_list):

        # because headers change with the programme
        topics_headers = self.get_headers_translation(csv_list[0].keys())
        _new = 0
        for index, topic in enumerate(csv_list):
            print('{fp} - topic {index}/{len}'.format(
                fp=fp,
                index=index, len=len(csv_list)),
                end='\r'
            )

            topic, created = Topic.objects.update_or_create(
                code=topic[topics_headers['code']],
                defaults={
                    'fp': fp,
                    'rcn': topic[topics_headers['rcn']],
                    'title': topic[topics_headers['title']],
                    'legalBasisRcn': topic[topics_headers['legalBasisRcn']] if (
                        'legalBasisRcn' in topics_headers and
                        topics_headers[
                            'legalBasisRcn']) in topic else '',
                    'legalBasisCode': topic[topics_headers['legalBasisCode']] if (
                            'legalBasisCode' in topics_headers and
                            topics_headers[
                                 'legalBasisCode']) in topic else '',
                    'source': self,
                }
            )
            _new += 1 if created else 0
        print('{fp} - {new} topics created, {index} processed'.format(
            fp=fp, new=_new, index=index + 1))

    def projects_to_objects(self, fp, csv_list):
        projects_headers = self.get_headers_translation(csv_list[0].keys())
        _new = 0

        for index, project in enumerate(csv_list):
            print('{fp} - project {index}/{len}'.format(
                fp=fp,
                index=index, len=len(csv_list)),
                end='\r'
            )
            try:
                start_date = datetime.datetime.strptime(
                    project[projects_headers['startDate']],
                    '%Y-%m-%d')
            except (KeyError, ValueError):
                try:
                    start_date = datetime.datetime.strptime(
                        project[projects_headers['startDate']],
                        '%d/%m/%Y')
                except (KeyError, ValueError):
                    start_date = None

            try:
                end_date = datetime.datetime.strptime(
                    project[projects_headers['endDate']],
                    '%Y-%m-%d')
            except (KeyError, ValueError):
                try:
                    end_date = datetime.datetime.strptime(
                        project[projects_headers['endDate']],
                        '%d/%m/%Y')
                except (KeyError, ValueError):
                    end_date = None

            call, created = Call.objects.update_or_create(
                title=project[projects_headers['call']],
                defaults={'fundingScheme': project[projects_headers['fundingScheme']], 'fp': fp, 'source': self}
            )

            try:
                topic = Topic.objects.get(code=project[projects_headers['topics']])
            except Topic.DoesNotExist:
                topic = None
                print('')
                print('GA {ga} - missing topic: {topics}'.format(
                    ga=project[projects_headers['GA']],
                    topics=project[projects_headers['topics']]))
                topic = Topic(code=project[projects_headers['topics']])
                topic.fp = fp
                topic.source = self
                topic.save()
                print(topic.id)
            try:
                total_cost = float(project[projects_headers['totalCost']].replace(",", "."))
            except ValueError:
                total_cost = 0

            try:
                ecMaxContribution = float(project[projects_headers['ecMaxContribution']].replace(",", "."))
            except ValueError:
                ecMaxContribution = 0

            try:
                UNICODE_EXISTS = bool(type(unicode))
            except NameError:
                unicode = str

            project_ob, created = Project.objects.update_or_create(
                rcn=project[projects_headers['rcn']],
                defaults={
                    'fp': fp,
                    'GA': project[projects_headers['GA']],
                    'acronym': project[projects_headers['acronym']],
                    'title': unicode(project[projects_headers['title']]),
                    'objective': unicode(project[projects_headers['objective']]),
                    'startDate': start_date,
                    'endDate': end_date,
                    'totalCost': total_cost,
                    'ecMaxContribution': ecMaxContribution,
                    'call': call,
                    'topic': topic,
                    'source': self,
                }
            )
            _new += 1 if created else 0

            for programme_code in project[projects_headers['programme']].split(';'):
                try:
                    project_ob.programme.add(Programme.objects.get(code=programme_code))
                    project_ob.save()
                except Programme.DoesNotExist:
                    print('')
                    print('GA {ga} - missing programme: {programme_code}'.format(ga=project_ob.GA, programme_code=programme_code))
                    _programme = Programme(code=programme_code)
                    _programme.fp = fp
                    _programme.source = self
                    _programme.save()
                    project_ob.programme.add(_programme)
                    project_ob.save()
        print('{fp} - {new} projects created, {index} processed'.format(
            fp=fp, new=_new, index=index + 1))

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

                print('\n', project_partner, _query, _query==Q(), Partner.objects.filter(
                    _query
                ))

                if _query == Q():
                    return None, False

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

    def select_multiple_partner(self, name, country, project_partner):
        try:
            return Partner.objects.get(
                legalName=name,
                country=country,
            )
        except Partner.MultipleObjectsReturned:
            # still multiple? I take the first
            print('\n multiple', name, project_partner,
                  Partner.objects.filter(
                      legalName=name,
                  ),
                  Partner.objects.filter(
                      legalName=name,
                      country=country,
                  ))
            p_res = {
                'len_partner_project': 0,
                'p_ob': None
            }

            for p in Partner.objects.filter(
                legalName=name,
                country=country,
            ):
                len_partner_project = len(PartnerProject.objects.filter(partner=p))
                if len_partner_project > p_res['len_partner_project']:
                    p_res['len_partner_project'] = len_partner_project
                    p_res['p_ob'] = p
            if p_res['p_ob']:
                return p_res['p_ob']
            else:
                return Partner.objects.filter(
                    legalName=name,
                    country=country,
                )[0]


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
                    partner_ob = self.select_multiple_partner(
                        name=project_partner[fp_organization_headers['name']],
                        country=project_partner[fp_organization_headers['country']],
                        project_partner=project_partner
                    )

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

    def organizations_to_objects(self, fp, csv_list):
        # because headers change with the programme
        organizations_headers = self.get_headers_translation(csv_list[0].keys())

        _new = 0
        # translates one row for each partner in one Partner object and one ParnerProject link
        for index, project_partner in enumerate(csv_list):
            print('{fp} - organizations {index}/{len}'.format(
                fp=fp,
                index=index, len=len(csv_list)),
                end='\r'
            )
            pic = project_partner[organizations_headers['id']]
            # in H2020 (almost) all partners have a pic. in fp7 appears to lead the legalname
            if fp == 'H2020':
                partner_ob, created = self.organization_dict_to_object(
                    pic,
                    project_partner,
                    organizations_headers, self
                )
            else:
                partner_ob, created = self.organization_dict_to_object_beforeh2020(
                    pic, project_partner, organizations_headers, self)
            if partner_ob:
                try:
                    ec_contribution = float(project_partner[organizations_headers['ecContribution']].replace(',', '.'))
                except ValueError:
                    # no contribution, will be 0
                    ec_contribution = 0

                project = Project.objects.get(rcn=project_partner[organizations_headers['rcn']])

                partnerproject, created = PartnerProject.objects.update_or_create(
                    partner=partner_ob, project=project,
                    defaults={
                        'coordinator': project_partner[organizations_headers['role']] == 'coordinator',
                        'ecContribution': ec_contribution,
                    }
                )
                _new += 1 if created else 0
        print('{fp} - {new} organizations created, {index} processed'.format(
            fp=fp, new=_new, index=index + 1))


# classes to hold track of the source of data
class EuodpData(models.Model, EuodpDataFileMethods, EuodpDataMethods):

    euodp_url = models.URLField()
    file_url = models.URLField()
    update_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return self.file_url

    def euodp_page(self):
        return self.euodp_url[:-4]

    def update(self, attribute_label, fp):
        with transaction.atomic():
            self.update_file()
            _filename = self.local_file()
            print(_filename)
            try:
                with open(_filename, encoding='utf-8') as csvfile:
                    csv_list = list(csv.DictReader(csvfile, delimiter=';', quotechar='"'))
            except UnicodeDecodeError:
                with open(_filename, encoding='latin-1') as csvfile:
                    csv_list = list(csv.DictReader(csvfile, delimiter=';', quotechar='"'))
            getattr(self, self.type_to_method[attribute_label])(fp, csv_list)
            self.save()


class FpData(models.Model):
    fp = models.CharField(max_length=5, choices=FP_CODE, default='H2020')

    organizations = models.ForeignKey(EuodpData, related_name='organizations', on_delete=models.SET_NULL, null=True)
    projects = models.ForeignKey(EuodpData, related_name='projects', on_delete=models.SET_NULL, null=True)
    programmes = models.ForeignKey(EuodpData, related_name='programmes', on_delete=models.SET_NULL, null=True)
    topics = models.ForeignKey(EuodpData, related_name='topics', on_delete=models.SET_NULL, null=True)

    def generate_euodpdata(self):

        for data in ['organizations', 'projects', 'programmes', 'topics']:
            if sourceurls[self.fp][data][1]:
                euodp_data = EuodpData()

                euodp_data.euodp_url = sourceurls[self.fp][data][1]
                euodp_data.file_url = sourceurls[self.fp][data][0]
                euodp_data.save()

                # sets the correct EuodpData object in FpData
                setattr(self, data, euodp_data)
        self.save()

    def __str__(self):
        return self.fp


class SourceData(models.Model):
    source = models.ForeignKey(EuodpData, on_delete=models.PROTECT)

    class Meta:
        abstract = True


class Partner(SourceData):
    CATEGORY_CODE = (
        (u'PRC', u'Private for-profit entities (excluding Higher or Secondary Education Establishments)'),
        (u'HES', u'Higher or Secondary Education Establishments'),
        (u'REC', u'Research Organisations'),
        (u'OTH', u'Other'),
        (u'PUB', u'Public bodies (excluding Research Organisations and Secondary or Higher Education Establishments)')
    )
    pic = models.CharField(max_length=20, default='')
    organizationActivityType = models.CharField(max_length=3, choices=CATEGORY_CODE)
    legalName = models.CharField(max_length=1024, blank=True, null=True)
    shortName = models.CharField(max_length=200, blank=True, null=True)

    street = models.CharField(max_length=200, blank=True, null=True)
    city = models.CharField(max_length=200, blank=True, null=True)
    country = models.CharField(max_length=8, blank=True, null=True)
    postalCode = models.CharField(max_length=8, blank=True, null=True)

    merged = models.BooleanField(default=False)
    merged_ids = models.CharField(max_length=200, validators=[validate_comma_separated_integer_list], blank=True,
                                  null=True)
    merged_with_id = models.IntegerField(blank=True,
                                         null=True)

    def __str__(self):
        if self.shortName:
            return u"{shortName} - {id}".format(shortName=self.shortName, id=self.pk)
        else:
            return u"{legalName}[...] - {id}".format(legalName=self.legalName[0:10], id=self.pk)

    def merge_with_models(self, alias_objects, keep_old=True):
        """
            "merges" to self the Partner objects stored in alias_objects as a list
        :param alias_objects: list of Partner objects to be merged
        :param keep_old: whether to delete the stale objects
        :return: nothing
        """
        if alias_objects:
            with transaction.atomic():
                if not isinstance(alias_objects, list)\
                        and not isinstance(alias_objects, QuerySet):
                    raise TypeError('the variable alias_objects needs to be a list object')

                if self.merged_ids is None:
                    _merged_ids = ''
                else:
                    _merged_ids = self.merged_ids + ','

                _merged_ids += ','.join([str(p_ob.id) for p_ob in alias_objects])

                for p_ob in alias_objects:
                    if not isinstance(p_ob, type(self)):
                        raise TypeError('one of the items of alias_objects ({ob}) is not a Partner object'.format(ob=p_ob))

                    if p_ob.merged_ids:
                        if ',' in p_ob.merged_ids:
                            _merged_ids += ','.join(p_ob.merged_ids.split(','))
                        _merged_ids += ',{pid}'.format(pid=p_ob.merged_ids)

                    if keep_old:
                        p_ob.merged = True
                        p_ob.merged_with_id = self.id
                        p_ob.save()

                        # sets the partner in project as self, noting the original
                        for pproject in PartnerProject.objects.filter(partner=p_ob):
                            pproject.partner = self
                            pproject.original_partner = p_ob
                            pproject.save()

                    else:
                        p_ob.delete()

                        # sets the partner in project as self
                        for pproject in PartnerProject.objects.filter(partner=p_ob):
                            pproject.partner = self
                            pproject.save()
                # it updates merged_ids only if the transaction was correctly carried out

                self.merged_ids = _merged_ids

                self.save()

    def get_absolute_url(self):
        return reverse('fprogramdb:project_list_id', kwargs={'partner_id': self.pk})


class Topic(SourceData):
    fp = models.CharField(max_length=5, choices=FP_CODE, default='H2020')
    rcn = models.CharField(max_length=20)
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200, blank=True, null=True)
    legalBasisRcn = models.CharField(max_length=20, blank=True, null=True)
    legalBasisCode = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return u"{code}".format(code=self.code)


class Call(SourceData):
    fp = models.CharField(max_length=2, choices=FP_CODE, default='H2020')
    title = models.CharField(max_length=200, blank=True, null=True)
    fundingScheme = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return u"{title}".format(title=self.title)


class Programme(SourceData):
    fp = models.CharField(max_length=2, choices=FP_CODE, default='H2020')
    rcn = models.CharField(max_length=20, primary_key=True)
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200, blank=True, null=True)
    shortTitle = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return u"{code}".format(code=self.code)


class Project(SourceData):
    fp = models.CharField(max_length=5, choices=FP_CODE, default='H2020')

    rcn = models.CharField(max_length=20, primary_key=True)
    GA = models.CharField(max_length=20)
    acronym = models.CharField(max_length=20)
    title = models.CharField(max_length=200, blank=True, null=True)
    objective = models.CharField(max_length=2048, blank=True, null=True)
    startDate = models.DateField(null=True, verbose_name="start date")
    endDate = models.DateField(null=True, verbose_name="end_date")
    totalCost = models.DecimalField(max_digits=13, decimal_places=2)
    ecMaxContribution = models.DecimalField(max_digits=13, decimal_places=2)
    duration = models.IntegerField(null=True, blank=True)
    programme = models.ManyToManyField(Programme)
    call = models.ForeignKey(Call, on_delete=models.PROTECT)
    topic = models.ForeignKey(Topic, on_delete=models.SET_NULL, blank=True, null=True)

    def __str__(self):
        if self.acronym:
            return u"{acronym}".format(acronym=self.acronym)
        else:
            if len(self.title) > 20:
                return u"{title}[..]".format(title=self.title[:20])
            else:
                return u"{title}".format(title=self.title)

    def partner_count(self):
        return PartnerProject.objects.filter(project=self).count()

    def get_absolute_url(self):
        return reverse('fprogramdb:project_data_rcn', kwargs={'rcn': self.rcn})


class PartnerProject(models.Model):

    coordinator = models.BooleanField()
    ecContribution = models.DecimalField(max_digits=13, decimal_places=2)

    partner = models.ForeignKey(Partner, on_delete=models.PROTECT)
    project = models.ForeignKey(Project, on_delete=models.PROTECT)

    original_partner = models.ForeignKey(Partner, on_delete=models.SET_NULL, related_name='original_partner', null=True)

    def __str__(self):
        return u"{project} - {partner}".format(
            partner=self.partner,
            project=self.project
        )
