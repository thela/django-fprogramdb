import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.decorators import method_decorator
from django.views import View

from fprogramdb.models import FpData
from fprogramdb.views import fprogramdb_basetemplate


class PopulateEuodpSourcesView(View):
    page_title = "PopulateEuodpSourcesView"
    template_name = "fprogramdb/manage/populate_euodp_data.html"

    # @method_decorator(login_required)
    # def post(self, request, pic=None, partner_id=None):
    @method_decorator(login_required)
    def get(self, request, fp):

        try:
            fp_data = FpData.objects.get(fp=fp)
        except FpData.DoesNotExist:
            return redirect('fprogramdb:frontpage')
        _context = {
            'page_name': self.page_title,
            'euodp_datas': [],
            'fprogramdb_basetemplate': fprogramdb_basetemplate
        }

        for attribute_label in ['programmes', 'topics', 'projects', 'organizations']:
            euodp_data = getattr(fp_data, attribute_label)
            if euodp_data:
                attribute_refresh_date = None
                if 'update' in request.GET and (
                        attribute_label in request.GET['update'] or 'all' in request.GET['update']):
                    euodp_data.update(attribute_label, fp)

                if 'check' in request.GET and (attribute_label in request.GET['check'] or 'all' in request.GET['check']):
                    attribute_refresh_date = euodp_data.check_updates()

                _context['euodp_datas'].append({
                    'attribute': attribute_label,
                    'euodp_data': euodp_data,
                    'refresh_date': attribute_refresh_date if isinstance(attribute_refresh_date,
                                                                         datetime.date) else '-',
                    'to_update': attribute_refresh_date > euodp_data.update_date if isinstance(
                        attribute_refresh_date, datetime.date) else '-',
                })

        return render(request, self.template_name, _context)
