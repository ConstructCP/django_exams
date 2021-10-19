from django import forms


class RegistrationForm(forms.Form):
    username = forms.CharField(label='User name', max_length=100)
    password = forms.CharField(
        label='Password', widget=forms.PasswordInput,
        validators=[])
