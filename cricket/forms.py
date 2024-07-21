from django import forms
from .models import  Team,Players

class TeamForms(forms.ModelForm):
    class Meta:
        model=Team
        fields= ['name','city']


class PlayersForms(forms.ModelForm):
    class Meta:
        model=Players
        fields=['name','age','experience','role','shirt_no']