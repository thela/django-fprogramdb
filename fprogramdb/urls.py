"""CordisReader URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from . import views

fpdb_patterns = ([
    url(r'^fp(?P<fp>[\D][\w]+)', views.ProjectListFP.as_view(), name="project_list_fp"),
    url(r'^pic(?P<pic>[0-9]+)', views.ProjectListPIC.as_view(), name="project_list_pic"),
    url(r'^partner(?P<partner_id>[0-9]+)', views.ProjectListID.as_view(), name="project_list_id"),
    url(r'^rcn(?P<rcn>[0-9]+)', views.ProjectListRCN.as_view(), name="project_data_rcn"),
], 'fprogramdb')

urlpatterns = [
    url(r'^', include(fpdb_patterns)),
]