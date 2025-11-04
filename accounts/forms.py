from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from .models import CustomUser


class UserRegistrationForm(UserCreationForm):
    """ Form for user registration. """

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Email'
        })
    )
    first_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )
    last_name = forms.CharField(
        required=True,
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )
    phone = forms.CharField(
        required=False,
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Phone (optional)'
        })
    )
    document_type = forms.ChoiceField(
        required=False,
        choices=[('', '---')] + list(CustomUser._meta.get_field('document_type').choices),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    document_number = forms.CharField(
        required=False,
        max_length=30,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Document Number (optional)'
        })
    )

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'email',
            'first_name',
            'last_name',
            'phone',
            'document_type',
            'document_number',
            'password1',
            'password2',
        ]
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })

    def clean_email(self):
        """ Validate if email is unique."""
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise ValidationError(_('This E-mail is already in use. Please use a different e-mail.'))
        return email

    def clean_document_number(self):
        """ Validate document number uniqueness, if provided. """
        document_number = self.cleaned_data.get('document_number')
        if document_number:
            if CustomUser.objects.filter(document_number=document_number).exists():
                raise ValidationError(_('This document number is already registered.'))
        return document_number

    def clean(self):
        """ Adittional validation for document fields. """
        cleaned_data = super().clean()
        document_type = cleaned_data.get('document_type')
        document_number = cleaned_data.get('document_number')

        # If one of them is filled, both must be filled.
        if (document_type and not document_number) or (document_number and not document_type):
            raise ValidationError(
                _('Both document type and number must be provided together.')
            )
        return cleaned_data


class UserLoginForm(AuthenticationForm):
    """ Custom Login Form with styled fields."""

    username = forms.Charfield(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Username or E-mail',
            'autofocus': True
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )


class UserProfileForm(forms.ModelForm):
    """ Form for editing user profile. """

    class Meta:
        model = CustomUser
        fields = [
            'first_name',
            'last_name',
            'email',
            'phone',
            'document_type',
            'document_number',
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def clean_email(self):
        """ Validate e-mail uniqueness excluding current user."""
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError(_('This e-mail is already in use.'))
        return email

    def clean_document_number(self):
        """ Validate document number uniqueness excluding current user. """
        document_number = self.cleaned_data.get('document_number')
        if document_number:
            if CustomUser.objects.filter(
                document_number=document_number
            ).exclude(pk=self.instance.pk).exisits():
                raise ValidationError(_('This document is already in use.'))
        return document_number
