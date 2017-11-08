from django.contrib import admin

# Register your models here.
from fprogramdb.models import Project, Call, Topic, Partner, PartnerProject, Programme, SourceFile


class ProjectAdmin(admin.ModelAdmin):
    search_fields = ['acronym', 'rcn']


class PartnerAdmin(admin.ModelAdmin):
    search_fields = ['legalName', 'shortName', 'pic']


admin.site.register(SourceFile)
admin.site.register(Project, ProjectAdmin)
admin.site.register(Call)
admin.site.register(Programme)
admin.site.register(Partner, PartnerAdmin)
admin.site.register(PartnerProject)
admin.site.register(Topic)
