from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Driver, DriverDocument


class DriverForm(forms.ModelForm):
    """Form for adding/editing drivers."""

    class Meta:
        model = Driver
        fields = [
            "first_name",
            "last_name",
            "cpf",
            "birth_date",
            "phone",
            "email",
            "address",
            "license_number",
            "license_category",
            "license_issue_date",
            "license_expiry_date",
            "hire_date",
            "status",
            "salary",
            "emergency_contact_name",
            "emergency_contact_phone",
            "notes",
        ]
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'cpf': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '000.000.000-00'}),
            'birth_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'license_number': forms.TextInput(attrs={'class': 'form-control'}),
            'license_category': forms.Select(attrs={'class': 'form-control'}),
            'license_issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'license_expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'hire_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class DriverDocumentForm(forms.ModelForm):
    """Form for driver documents."""

    class Meta:
        model = DriverDocument
        fields = [
            "driver",
            "document_type",
            "document_number",
            "issue_date",
            "expiry_date",
            "issuing_authority",
            "file",
            "notes",
        ]
        widgets = {
            'driver': forms.Select(attrs={'class': 'form-control'}),
            'document_type': forms.Select(attrs={'class': 'form-control'}),
            'document_number': forms.TextInput(attrs={'class': 'form-control'}),
            'issue_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'issuing_authority': forms.TextInput(attrs={'class': 'form-control'}),
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }
