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
    url(r'^fp(?P<fp>[\D][\w]+)', views.project_list_fp, name="project_list_fp"),
    url(r'^pic(?P<pic>[0-9]+)', views.project_list_pic, name="project_list_pic"),
    url(r'^rcn(?P<rcn>[0-9]+)', views.project_data_rcn, name="project_data_rcn"),
], 'fprogramdb')

urlpatterns = [
    url(r'^', include(fpdb_patterns)),
]