from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Employee, DriverProfile, SecurityProfile, EmployeeDocument


class EmployeeForm(forms.ModelForm):
    """Form for creating/editing employees."""

    class Meta:
        model = Employee
        fields = [
            "employee_type",
            "employee_number",
            "full_name",
            "cpf",
            "rg",
            "birth_date",
            "gender",
            "phone",
            "email",
            "address",
            "city",
            "state",
            "zip_code",
            "hire_date",
            "status",
            "salary",
            "payment_cycle",
            "payment_method",
            "bank_name",
            "bank_branch",
            "bank_account",
            "emergency_contact_name",
            "emergency_contact_relationship",
            "emergency_contact_phone",
            "photo",
            "notes",
        ]
        widgets = {
            "employee_type": forms.Select(attrs={"class": "form-control"}),
            "employee_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("Auto-generated if empty"),
                }
            ),
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "cpf": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "000.000.000-00"}
            ),
            "rg": forms.TextInput(attrs={"class": "form-control"}),
            "birth_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "gender": forms.Select(attrs={"class": "form-control"}),
            "phone": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "address": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "state": forms.TextInput(attrs={"class": "form-control", "maxlength": 2}),
            "zip_code": forms.TextInput(attrs={"class": "form-control"}),
            "hire_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "status": forms.Select(attrs={"class": "form-control"}),
            "salary": forms.NumberInput(attrs={"class": "form-control"}),
            "payment_cycle": forms.Select(attrs={"class": "form-control"}),
            "payment_method": forms.Select(attrs={"class": "form-control"}),
            "bank_name": forms.TextInput(attrs={"class": "form-control"}),
            "bank_branch": forms.TextInput(attrs={"class": "form-control"}),
            "bank_account": forms.TextInput(attrs={"class": "form-control"}),
            "emergency_contact_name": forms.TextInput(attrs={"class": "form-control"}),
            "emergency_contact_relationship": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "emergency_contact_phone": forms.TextInput(attrs={"class": "form-control"}),
            "photo": forms.FileInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class DriverProfileForm(forms.ModelForm):
    """Form for driver profile."""

    class Meta:
        model = DriverProfile
        fields = [
            "employee",
            "license_number",
            "license_category",
            "license_issue_date",
            "license_expiry_date",
            "license_first_issue_date",
            "has_mopp",
            "mopp_expiry_date",
            "has_defensive_driving",
            "defensive_driving_date",
            "last_medical_exam_date",
            "next_medical_exam_date",
            "blood_type",
            "notes",
        ]
        widgets = {
            "employee": forms.Select(attrs={"class": "form-control"}),
            "license_number": forms.TextInput(attrs={"class": "form-control"}),
            "license_category": forms.Select(attrs={"class": "form-control"}),
            "license_issue_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "license_expiry_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "license_first_issue_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "has_mopp": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "mopp_expiry_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "has_defensive_driving": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "defensive_driving_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "last_medical_exam_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "next_medical_exam_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "blood_type": forms.Select(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter employees to show only drivers
        self.fields["employee"].queryset = Employee.objects.filter(
            employee_type="driver"
        )


class SecurityProfileForm(forms.ModelForm):
    """Form for security profile."""

    class Meta:
        model = SecurityProfile
        fields = [
            "employee",
            "security_license_number",
            "security_license_issue_date",
            "security_license_expiry_date",
            "has_firearms_license",
            "firearms_license_number",
            "firearms_license_expiry",
            "has_vigilant_course",
            "vigilant_course_date",
            "has_recycling_course",
            "recycling_course_date",
            "next_recycling_date",
            "last_medical_exam_date",
            "next_medical_exam_date",
            "specializations",
            "notes",
        ]
        widgets = {
            "employee": forms.Select(attrs={"class": "form-control"}),
            "security_license_number": forms.TextInput(attrs={"class": "form-control"}),
            "security_license_issue_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "security_license_expiry_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "has_firearms_license": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "firearms_license_number": forms.TextInput(attrs={"class": "form-control"}),
            "firearms_license_expiry": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "has_vigilant_course": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "vigilant_course_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "has_recycling_course": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
            "recycling_course_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "next_recycling_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "last_medical_exam_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "next_medical_exam_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "specializations": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter employees to show only security guards
        self.fields["employee"].queryset = Employee.objects.filter(
            employee_type="security"
        )


class EmployeeDocumentForm(forms.ModelForm):
    """Form for employee documents."""

    class Meta:
        model = EmployeeDocument
        fields = [
            "employee",
            "document_type",
            "document_number",
            "issue_date",
            "expiry_date",
            "issuing_authority",
            "file",
            "notes",
        ]
        widgets = {
            "employee": forms.Select(attrs={"class": "form-control"}),
            "document_type": forms.Select(attrs={"class": "form-control"}),
            "document_number": forms.TextInput(attrs={"class": "form-control"}),
            "issue_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "expiry_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "issuing_authority": forms.TextInput(attrs={"class": "form-control"}),
            "file": forms.FileInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


""" from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Driver, DriverDocument


class DriverForm(forms.ModelForm):
    '''Form for adding/editing drivers.'''

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
    '''Form for driver documents.'''

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
 """
