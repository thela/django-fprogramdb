from django.shortcuts import render

from django.conf import settings
from fprogramdb.models import Partner, PartnerProject, Project

if hasattr(settings, 'FPROGRAMDB_BASETEMPLATE'):
    fprogramdb_basetemplate = settings.FPROGRAMDB_BASETEMPLATE
else:
    fprogramdb_basetemplate = "fprogramdb/base.html"


def project_list_fp(request, fp):
    projects = Project.objects.filter(fp=fp).order_by('startDate')
    return render(request, "fprogramdb/project_list_fp.html", {
        'title': 'List of projects within {fp}'.format(fp=fp),
        'projects': [
            {
                'data': [_p.fp, str(_p), _p.startDate, _p.ecMaxContribution],
                'rcn': _p.rcn
            }
            for _p in projects],
        'fprogramdb_basetemplate': fprogramdb_basetemplate
    })


def project_list_pic(request, pic):
    partnerprojects = PartnerProject.objects.filter(partner__pic=pic).order_by('project__startDate')
    partner = Partner.objects.get(pic=pic)
    return render(request, "fprogramdb/project_list_pic.html", {
        'title': 'List of project with {acronym} in partnership'.format(acronym=partner.shortName),
        'projects': [
            {
                'data': [pp.project.fp, pp.project.acronym, pp.project.startDate, pp.ecContribution, pp.coordinator],
                'rcn': pp.project.rcn
            }
            for pp in partnerprojects],
        'partner': partner,
        'fprogramdb_basetemplate': fprogramdb_basetemplate
    })


def project_list_id(request, partner_id):
    partnerprojects = PartnerProject.objects.filter(partner__id=partner_id).order_by('project__startDate')
    partner = Partner.objects.get(id=partner_id)
    return render(request, "fprogramdb/project_list_pic.html", {
        'title': 'List of project with {acronym} in partnership'.format(acronym=partner.shortName),
        'projects': [
            {
                'data': [pp.project.fp, pp.project.acronym, pp.project.startDate, pp.ecContribution, pp.coordinator],
                'rcn': pp.project.rcn
            }
            for pp in partnerprojects],
        'partner': partner,
        'fprogramdb_basetemplate': fprogramdb_basetemplate
    })


def project_data_rcn(request, rcn):
    project = Project.objects.get(
        rcn=rcn
    )
    return render(request, "fprogramdb/project_data_rcn.html", {
        'title': 'Detail of project {acronym}'.format(acronym=project.acronym),
        'project': project,
        'partnerprojects': PartnerProject.objects.filter(project=project),
        'fprogramdb_basetemplate': fprogramdb_basetemplate
    })
