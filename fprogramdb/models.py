from __future__ import unicode_literals

from django.core.validators import validate_comma_separated_integer_list
from django.db import models, transaction
from django.db.models.query import QuerySet

FP_CODE = (
    (u'FP6', u'FP6'),
    (u'FP7', u'FP7'),
    (u'H2020', u'H2020'),
)


class SourceFile(models.Model):
    euodp_url = models.URLField()
    file_url = models.URLField()
    update_date = models.DateField(blank=True, null=True)

    def __unicode__(self):
        return self.euodp_url


class Partner(models.Model):
    # TODO keep track of inherited deletions

    # TODO warn for potential loss of external models
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

    def __unicode__(self):
        if self.shortName:
            return u"{shortName} - {id}".format(shortName=self.shortName, id=self.id)
        else:
            return u"{legalName}[...] - {id}".format(legalName=self.legalName[0:10], id=self.id)

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


class Topic(models.Model):
    fp = models.CharField(max_length=5, choices=FP_CODE, default='H2020')
    rcn = models.CharField(max_length=20)
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200, blank=True, null=True)
    legalBasisRcn = models.CharField(max_length=20)
    legalBasisCode = models.CharField(max_length=20)

    def __unicode__(self):
        return u"{code}".format(code=self.code)


class Call(models.Model):
    fp = models.CharField(max_length=2, choices=FP_CODE, default='H2020')
    title = models.CharField(max_length=200, blank=True, null=True)
    fundingScheme = models.CharField(max_length=200, blank=True, null=True)

    def __unicode__(self):
        return u"{title}".format(title=self.title)


class Programme(models.Model):
    fp = models.CharField(max_length=2, choices=FP_CODE, default='H2020')
    rcn = models.CharField(max_length=20, primary_key=True)
    code = models.CharField(max_length=20)
    title = models.CharField(max_length=200, blank=True, null=True)
    shortTitle = models.CharField(max_length=200, blank=True, null=True)

    def __unicode__(self):
        return u"{code}".format(code=self.code)


class Project(models.Model):
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
    call = models.ForeignKey(Call)
    topic = models.ForeignKey(Topic, blank=True, null=True)

    def __unicode__(self):
        if self.acronym:
            return u"{acronym}".format(acronym=self.acronym)
        else:
            if len(self.title) > 20:
                return u"{title}[..]".format(title=self.title[:20])
            else:
                return u"{title}".format(title=self.title)


class PartnerProject(models.Model):

    coordinator = models.BooleanField()
    ecContribution = models.DecimalField(max_digits=13, decimal_places=2)

    partner = models.ForeignKey(Partner)
    project = models.ForeignKey(Project)

    original_partner = models.ForeignKey(Partner, related_name='original_partner', null=True)

    def __unicode__(self):
        return u"{project} - {partner}".format(
            partner=self.partner,
            project=self.project
        )

