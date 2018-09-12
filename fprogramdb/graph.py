import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View

from fprogramdb.models import Programme, Partner, PartnerProject
from fprogramdb.views import fprogramdb_basetemplate


class PicHist(View):
    template_name = "fprogramdb/graph/scheme_hist.html"
    title = 'List of project with {acronym} in partnership'

    def yearly_bin(self, project):
        return datetime.date(
                year=project.startDate.year,
                month=1,
                day=1
            )

    def halfyear_bin(self, project):
        if project.startDate.month <= 6:

            return datetime.date(
                    year=project.startDate.year,
                    month=1,
                    day=1
                )
        else:
            return datetime.date(
                    year=project.startDate.year,
                    month=7,
                    day=1
                )

    def monthly_bin(self, project):
        return datetime.date(
                year=project.startDate.year,
                month=project.startDate.month,
                day=1
            )

    def compose_graph_data(
            self,
            partnerprojects, timespan='yearly',
            data_type='number'
    ):
        timespan_methods = {
            'yearly': self.yearly_bin,
            'halfyearly': self.halfyear_bin,
            'monthly': self.monthly_bin
        }

        _res = {}
        for partnerproject in partnerprojects:
            _bin = timespan_methods[timespan](partnerproject.project)
            if _bin in _res:
                if partnerproject.coordinator:
                    if data_type == 'contribution':
                        _res[_bin]['values'][1] += float(partnerproject.ecContribution)  # 1
                    elif data_type == 'number':
                        _res[_bin]['values'][1] += 1
                    _res[_bin]['projects'][1].append([
                        partnerproject.project.rcn, partnerproject.project.acronym
                    ])
                else:
                    if data_type == 'contribution':
                        _res[_bin]['values'][0] += float(partnerproject.ecContribution)  # 1
                    elif data_type == 'number':
                        _res[_bin]['values'][0] += 1
                    _res[_bin]['projects'][0].append([
                        partnerproject.project.rcn, partnerproject.project.acronym
                    ])

            else:
                _res[_bin] = {
                    'values': [0, 0],
                    'projects': [[], []],
                    'projects_numbers': [],
                    'label': _bin
                }
        return _res

    @method_decorator(login_required)
    def get(self, request, pic=None, partner_id=None):
        if pic:
            partner = Partner.objects.get(pic=pic, merged=False)
        elif partner_id:
            partner = Partner.objects.get(id=partner_id, merged=False)
        if not partner:
            raise Partner.DoesNotExist
        context = {
            'fprogramdb_basetemplate': fprogramdb_basetemplate,
            'title': self.title.format(acronym=partner.shortName),
            'page_name': self.title.format(acronym=partner.shortName),
        }

        timespan = 'yearly'
        if 'timespan' in request.GET and request.GET['timespan'] in [
                'yearly',
                'halfyearly',
                'monthly']:
            timespan = request.GET['timespan']

        data_type = 'number'
        if 'data_type' in request.GET and request.GET['data_type'] in [
                'number',
                'contribution']:
            data_type = request.GET['data_type']

        partnerprojects = PartnerProject.objects.filter(
            partner=partner,

        ).order_by('project__startDate')

        _res = self.compose_graph_data(partnerprojects, timespan, data_type)

        context.update({
            'partner': partner,
            'barchart': {

                'title': self.title.format(acronym=partner.shortName),
                'labels': [key for key in _res],
                'series': [
                    [_res[key]['values'][0] for key in _res],
                    [_res[key]['values'][1] for key in _res]],
            },
            'table_data':
                [{
                    'label': key,
                    'label_ext': _res[key]['label'],
                    'data': [
                        {
                            'value': _res[key]['values'][data_series_index],
                            'projects': _res[key]['projects'][data_series_index]
                        } for data_series_index in [0, 1]
                    ]

                } for key in _res],
            'series_label': [
                'Month',
                '{acronym} in partnership'.format(acronym=partner.shortName),
                'coordinated by {acronym}'.format(acronym=partner.shortName)],

        })

        return render(request, self.template_name, context)