"""fprogramdb URL Configuration
"""
from django.conf.urls import url, include
from django.urls import path, re_path

from . import views, manage, graph

app_name = 'fprogramdb'

fpdb_patterns = [
    re_path(r'^fp(?P<fp>[\D][\w]+)', views.ProjectListFP.as_view(), name="project_list_fp"),
    path(r'pic<int:pic>', views.DetailPIC.as_view(), name="detail_pic"),
    path(r'pic<int:pic>/edit', views.EditPIC.as_view(), name="edit_pic"),
    path(r'pic<int:pic>/project_list', views.ProjectListPIC.as_view(), name="project_list_pic"),
    path(r'partner<int:partner_id>', views.DetailPIC.as_view(), name="detail_id"),
    path(r'partner<int:partner_id>/edit', views.EditPIC.as_view(), name="edit_id"),
    path(r'partner<int:partner_id>/project_list', views.ProjectListPIC.as_view(), name="project_list_id"),
    path(r'pic<int:pic>', views.DetailPIC.as_view(), name="detail_pic"),
    path(r'rcn<int:rcn>', views.ProjectDataRCN.as_view(), name="project_data_rcn"),
    path(r'', views.FrontPage.as_view(), name="frontpage"),
]

fpdb_graph_patterns = [
    path('graph/pic<int:pic>', graph.PicHist.as_view(), name="hist_pic"),
    path('graph/partner<int:partner_id>', graph.PicHist.as_view(), name="hist_id"),
]

fpdb_manage_patterns = [
    path('manage/euodp_sources_fp<fp>', manage.PopulateEuodpSourcesView.as_view(), name="euodp_sources")
]

urlpatterns = [
    path('', include(fpdb_graph_patterns)),
    path('', include(fpdb_manage_patterns)),
    path('', include(fpdb_patterns)),
]
