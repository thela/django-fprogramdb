from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View


class PopulateEuodpSourcesView(View):
    page_title = "PopulateEuodpSourcesView"
    template_name = "fprogramdb/manage/populate_euodp_data.html"

    #@method_decorator(login_required)
    #def post(self, request, pic=None, partner_id=None):
    @method_decorator(login_required)
    def get(self, request):
        _context = {
            'page_title': self.page_title
        }
        return render(request, self.template_name, _context)