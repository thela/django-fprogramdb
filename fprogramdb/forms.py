from django import forms
from fprogramdb.models import Partner


class PartnerForm(forms.ModelForm):
    class Meta:
        model = Partner
        exclude = [
            'source', 'pic',
            'merged', 'merged_ids', 'merged_with_id',
        ]

    def __init__(self, *args, **kwargs):
        super(PartnerForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

class PartnerId(forms.Form):
    partner_id = forms.IntegerField()


class PartnerSelect(forms.Form):
    selected = forms.BooleanField()
    partner_id = forms.IntegerField()
    pic = forms.IntegerField(required=False)
    shortName = forms.CharField(max_length=255, required=False)
    legalName = forms.CharField(max_length=255)
    project_number = forms.IntegerField(required=False)


class PartnerSearch(forms.Form):
    search_field = forms.CharField(max_length=255, required=True)
