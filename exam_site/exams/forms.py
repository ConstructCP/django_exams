from django import forms

from .models import ApplicationUser


class RegistrationForm(forms.ModelForm):
    """ Form for user registration """
    class Meta:
        model = ApplicationUser
        fields = ['username', 'password']
        widgets = {'password': forms.PasswordInput()}
