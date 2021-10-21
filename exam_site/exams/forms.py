from django import forms

from .models import ApplicationUser


class RegistrationForm(forms.ModelForm):
    class Meta:
        model = ApplicationUser
        fields = ['username', 'password']
        widgets = {'password': forms.PasswordInput()}
