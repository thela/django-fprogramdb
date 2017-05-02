from django.contrib import admin

# Register your models here.
from fprogramdb.models import Project, Call, Topic, Partner, PartnerProject, Programme, SourceFile

admin.site.register(SourceFile)
admin.site.register(Project)
admin.site.register(Call)
admin.site.register(Programme)
admin.site.register(Partner)
admin.site.register(PartnerProject)
admin.site.register(Topic)
