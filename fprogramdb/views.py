# -*- coding: utf-8 -*-
from __future__ import print_function

import difflib

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.forms import formset_factory
from django.shortcuts import render, redirect

from django.conf import settings
from django.utils.decorators import method_decorator
from django.views import View
from .forms import PartnerSelect, PartnerId, PartnerForm, PartnerSearch

from .models import Partner, PartnerProject, Project, FpData, FP_CODE

if hasattr(settings, 'FPROGRAMDB_BASETEMPLATE'):
    fprogramdb_basetemplate = settings.FPROGRAMDB_BASETEMPLATE
else:
    fprogramdb_basetemplate = "fprogramdb/base.html"


class ProjectListFP(View):
    template_name = "fprogramdb/project_list_fp.html"

    @method_decorator(login_required)
    def get(self, request, fp):
        projects = Project.objects.filter(fp=fp).order_by('startDate')
        return render(request, self.template_name, {
            'page_name': 'List of projects within {fp}'.format(fp=fp),
            'projects': [
                {
                    'data': [_p.fp, str(_p), _p.startDate, _p.ecMaxContribution],
                    'rcn': _p.rcn
                }
                for _p in projects],
            'fprogramdb_basetemplate': fprogramdb_basetemplate
        })


class FrontPage(View):
    template_name = "fprogramdb/front_page.html"

    @method_decorator(login_required)
    def get(self, request):
        #TODO show details of last update
        _context = {
            'page_name': 'List of Framework Programs',
            'fp_data': [],
            'fprogramdb_basetemplate': fprogramdb_basetemplate
        }
        for fp_label in FP_CODE:
            try:
                _data = FpData.objects.get(fp=fp_label[1])
                _context['fp_data'].append({
                    'data': _data,
                    'num_projects': Project.objects.filter(fp=fp_label[1]).count(),
                    'num_partners': PartnerProject.objects.filter(
                        project__fp=fp_label[1],
                        partner__merged=False).count(),
                    'ecMaxContribution': Project.objects.filter(fp=fp_label[1]).aggregate(Sum('ecMaxContribution'))['ecMaxContribution__sum']
                })
            except (KeyError, FpData.DoesNotExist):
                pass
        return render(request, self.template_name, _context)


class DetailPIC(View):
    template_name = "fprogramdb/detail_pic.html"
    title = 'Detail of Partner {acronym}'

    @method_decorator(login_required)
    def get(self, request, pic, partnerformset=None, results_from_searchfield=None):
        partner = Partner.objects.get(pic=pic)

        _context = {
            'page_name': self.title.format(acronym=partner.shortName),
            'fprogramdb_basetemplate': fprogramdb_basetemplate,
            'partner': partner,
        }

        if partner.merged_ids:
            _context['merged_ids'] = [Partner.objects.get(id=_id) for _id in partner.merged_ids.split(',')]

        return render(request, self.template_name, _context)


class EditPIC(View):
    template_name = "fprogramdb/edit_pic.html"
    title = 'Edit of project with {acronym} in partnership'

    @method_decorator(login_required)
    def post(self, request, pic):
        partner = Partner.objects.get(pic=pic)
        partnerform = PartnerForm(request.POST, request.FILES, instance=partner)
        if 'Save' in request.POST:
            if partnerform.is_valid():
                partnerform.save()
                return redirect('fprogramdb:detail_pic', pic=pic)

        return self.get(request, partner, partnerform)

    @method_decorator(login_required)
    def get(self, request, pic, partner=None, partnerform=None):
        if not partner:
            partner = Partner.objects.get(pic=pic)
        if not partnerform:
            partnerform = PartnerForm(instance=partner)

        _context = {
            'page_name': self.title.format(acronym=partner.shortName),
            'fprogramdb_basetemplate': fprogramdb_basetemplate,
            'partner': partner,
            'partnerform': partnerform,
        }

        if partner.merged_ids:
            _context['merged_ids'] = [Partner.objects.get(id=_id) for _id in partner.merged_ids.split(',')]

        return render(request, self.template_name, _context)


class ProjectListPIC(View):
    template_name = "fprogramdb/project_list_pic.html"
    title = 'List of project with {acronym} in partnership'

    @staticmethod
    def similar(seq1, seq2):
        return difflib.SequenceMatcher(a=seq1.lower(), b=seq2.lower()).ratio()

    @method_decorator(login_required)
    def post(self, request, pic=None, partner_id=None):
        _context = {'partner_form': {}}
        formset = None
        partners_id = []

        if pic:
            partner = Partner.objects.get(pic=pic)
        elif partner_id:
            partner = Partner.objects.get(id=partner_id)

        partnerformset = formset_factory(PartnerSelect, extra=0)
        partneridset = formset_factory(PartnerId, extra=0)
        partner_search_form = PartnerSearch(request.POST, request.FILES)

        if request.method == 'POST':
            if 'MergeView' in request.POST:
                formset = partnerformset(request.POST, prefix="merge_view")
                for form in formset:
                    if form.is_valid():
                        partners_id.append(form.cleaned_data['partner_id'])

                _res = []
                _initial = []
                for _partner_id in partners_id:
                    try:
                        from django.db import DEFAULT_DB_ALIAS
                        from django.contrib.admin.utils import NestedObjects
                        from django.utils.encoding import force_text
                        from django.template.defaultfilters import capfirst

                        using = DEFAULT_DB_ALIAS

                        obj = Partner.objects.get(id=_partner_id)  # the object you are going to delete

                        collector = NestedObjects(using=using)
                        collector.collect([obj])

                        def format_callback(_obj):
                            opts = _obj._meta

                            return u'{model_name}: {instance_name}'.format(
                                model_name=capfirst(opts.verbose_name),
                                instance_name=force_text(_obj)
                            )

                        model_count = {model._meta.verbose_name_plural: len(objs) for model, objs in
                                       collector.model_objs.items()}

                        _res.append([
                            obj,
                            collector.nested(format_callback),
                            dict(model_count).items(),
                            PartnerForm(instance=obj)
                        ])
                        _initial.append({
                            'partner_id': _partner_id,
                        })
                    except Partner.DoesNotExist:
                        pass
                _context['partner_form']['merging_partner_formdata'] = _res
                _context['partner_form']['selected_formset'] = partneridset(initial=_initial, prefix="selected")

            elif 'Merge' in request.POST:
                formset_selected = partneridset(request.POST, request.FILES, prefix="selected")
                alias_objects = []
                for form in formset_selected:
                    if form.is_valid():
                        try:
                            alias_objects.append(
                                Partner.objects.get(id=form.cleaned_data['partner_id'], merged=False)
                            )
                        except Partner.DoesNotExist:
                            pass
                dest_object = Partner.objects.get(pic=pic)
                dest_object.merge_with_models(alias_objects)
                if pic:
                    return redirect('fprogramdb:project_list_pic', pic=pic)
                elif partner_id:
                    return redirect('fprogramdb:project_list_id', pic=partner_id)

            elif 'Search' in request.POST:
                partner_search_form = PartnerSearch(request.POST, request.FILES)
                if partner_search_form.is_valid():
                    test = partner_search_form.cleaned_data['search_field']
                    _initial = []
                    for p in Partner.objects.exclude(
                            id=partner.id).filter(merged=False):

                        sim = self.similar(test, p.legalName)
                        if sim > .7:

                            _initial.append({
                                'selected': False,
                                'partner_id': p.id,
                                'pic': p.pic,
                                'shortName': p.shortName,
                                'legalName': p.legalName,
                                'project_number': PartnerProject.objects.filter(partner=p).count()
                            })
                    formset = partnerformset(initial=_initial, prefix="merge_view")

        _context.update({
            'page_name': 'List of project with {acronym} in partnership'.format(acronym=partner.shortName),
            'partner': partner,
            'merge_view_formset': formset,
            'partner_search_form': partner_search_form,
            'fprogramdb_basetemplate': fprogramdb_basetemplate,
        })
        return render(request, self.template_name, _context)

    @method_decorator(login_required)
    def get(self, request, pic=None, partner_id=None, partnerformset=None, results_from_searchfield=None):
        if pic:
            partner = Partner.objects.get(pic=pic)
        elif partner_id:
            partner = Partner.objects.get(id=partner_id)
        else:
            pass

        _context = {
            'page_name': self.title.format(acronym=partner.shortName),
            'fprogramdb_basetemplate': fprogramdb_basetemplate,
            'partner': partner,
            'partner_search_form': PartnerSearch()
        }

        if 'similarity' in request.GET:
            if not partnerformset:
                partnerformset = formset_factory(PartnerSelect, extra=0)
            test = request.GET['similarity']
            _initial = []
            for p in Partner.objects.exclude(
                    id=partner.id).filter(merged=False):
                sim = self.similar(getattr(p, test), getattr(partner, test))
                if sim > .7:

                    _initial.append({
                        'selected': False,
                        'partner_id': p.id,
                        'pic': p.pic,
                        'shortName': p.shortName,
                        'legalName': p.legalName,
                        'project_number': PartnerProject.objects.filter(partner=p).count()
                    })
            _context['merge_view_formset'] = partnerformset(initial=_initial, prefix="merge_view")
        elif partner.merged:
            _context['initial_projects'] = [
                {
                    'data': [pp.project.fp, pp.project.acronym, pp.project.startDate, pp.project.endDate,
                             pp.ecContribution, pp.project.partner_count, pp.coordinator],
                    'rcn': pp.project.rcn
                }
                for pp in PartnerProject.objects.filter(original_partner=partner).order_by('project__startDate')]
        else:
            _context['projects'] = [
                {
                    'data': [pp.project.fp, pp.project.acronym, pp.project.startDate, pp.project.endDate,
                             pp.ecContribution, pp.project.partner_count, pp.coordinator],
                    'rcn': pp.project.rcn
                }
                for pp in PartnerProject.objects.filter(partner=partner).order_by('project__startDate')]

        if partner.merged_ids:
            _context['merged_ids'] = [Partner.objects.get(id=_id) for _id in partner.merged_ids.split(',')]
        return render(request, self.template_name, _context)


class ProjectDataRCN(View):
    template_name = "fprogramdb/project_data_rcn.html"

    @method_decorator(login_required)
    def get(self, request, rcn):
        project = Project.objects.get(
            rcn=rcn
        )
        return render(request, "fprogramdb/project_data_rcn.html", {
            'page_name': 'Detail of project {acronym}'.format(acronym=project.acronym),
            'project': project,
            'partnerprojects': PartnerProject.objects.filter(project=project),
            'fprogramdb_basetemplate': fprogramdb_basetemplate
        })
