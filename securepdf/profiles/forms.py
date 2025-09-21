from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'phone', 'aadhar', 'pan', 'school', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class':'w-full rounded-md border px-3 py-2'}),
            'email': forms.EmailInput(attrs={'class':'w-full rounded-md border px-3 py-2'}),
            'phone': forms.TextInput(attrs={'class':'w-full rounded-md border px-3 py-2'}),
            'aadhar': forms.TextInput(attrs={'class':'w-full rounded-md border px-3 py-2'}),
            'pan': forms.TextInput(attrs={'class':'w-full rounded-md border px-3 py-2'}),
            'school': forms.TextInput(attrs={'class':'w-full rounded-md border px-3 py-2'}),
            'password1': forms.PasswordInput(attrs={'class':'w-full rounded-md border px-3 py-2'}),
            'password2': forms.PasswordInput(attrs={'class':'w-full rounded-md border px-3 py-2'}),
        }

class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class':'w-full rounded-md border px-3 py-2'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'w-full rounded-md border px-3 py-2'}))
