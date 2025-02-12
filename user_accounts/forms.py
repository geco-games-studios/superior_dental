from django import forms
from django.contrib.auth.forms import UserCreationForm
from user_accounts.models import CustomUser
from .models import Dentist, Staff

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser  # Use the custom user model
        fields = ('username', 'email', 'password1', 'password2', 'user_type')  # Include additional fields if needed

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if CustomUser.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("A user with that username already exists.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with that email already exists.")
        return email
    

class DentistForm(forms.ModelForm):
    class Meta:
        model = Dentist
        fields = ['specialization', 'contact_number', 'available_days']

class StaffForm(forms.ModelForm):
    class Meta:
        model = Staff
        fields = ['role', 'contact_number']