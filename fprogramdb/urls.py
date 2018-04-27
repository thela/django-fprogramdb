"""fprogramdb URL Configuration
"""
from django.conf.urls import url, include

from . import views, manage

app_name = 'fprogramdb'

fpdb_patterns = [
    url(r'^fp(?P<fp>[\D][\w]+)', views.ProjectListFP.as_view(), name="project_list_fp"),
    url(r'^pic(?P<pic>[0-9]+)', views.ProjectListPIC.as_view(), name="project_list_pic"),
    url(r'^partner(?P<partner_id>[0-9]+)', views.ProjectListPIC.as_view(), name="project_list_id"),
    url(r'^rcn(?P<rcn>[0-9]+)', views.ProjectDataRCN.as_view(), name="project_data_rcn"),
    url(r'^', views.FrontPage.as_view(), name="frontpage"),
]

fpdb_manage_patterns = [
    url(r'manage/euodp_sources', manage.PopulateEuodpSourcesView.as_view(), name="")
    ]

urlpatterns = [
    url(r'^', include(fpdb_patterns)),
    url(r'^', include(fpdb_manage_patterns)),
]
