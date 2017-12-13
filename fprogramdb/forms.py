from django import forms
from fprogramdb.models import Partner


class PartnerForm(forms.ModelForm):
    class Meta:
        model = Partner
        fields = '__all__'


class PartnerId(forms.Form):
    partner_id = forms.IntegerField()


class PartnerSelect(forms.Form):
    selected = forms.BooleanField()
    partner_id = forms.IntegerField()
    pic = forms.IntegerField(required=False)
    shortName = forms.CharField(max_length=255, required=False)
    legalName = forms.CharField(max_length=255)


class PartnerSearch(forms.Form):
    search_field = forms.CharField(max_length=255, required=True)
