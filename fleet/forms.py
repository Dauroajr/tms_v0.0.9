from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    Vehicle,
    VehicleAssignment,
    VehicleBrand,
    VehicleDocument,
    Driver,
    DriverDocument,
    MaintenanceRecord,
)


class VehicleBrandForm(forms.ModelForm):
    """Form for adding/editing vehicle brands."""

    class Meta:
        model = VehicleBrand
        fields = ["name", "country", "logo", "is_active", "notes"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("e.g., Volvo, Mercedes"),
                }
            ),
            "country": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": _("e.g., Sweden, Germany"),
                }
            ),
            "logo": forms.FileInput(attrs={"class": "form-control"}),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class VehicleForm(forms.ModelForm):
    """Form for adding/editing vehicles."""

    class Meta:
        model = Vehicle
        fields = [
            "brand",
            "model",
            "plate",
            "type",
            "year",
            "color",
            "capacity_kg",
            "capacity_m3",
            "fuel_type",
            "chassis_number",
            "renavam",
            "status",
            "purchase_date",
            "purchase_value",
            "current_km",
            "notes",
        ]
        widgets = {
            "plate": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "ABC1D23"}
            ),
            "type": forms.Select(attrs={"class": "form-control"}),
            "brand": forms.TextInput(attrs={"class": "form-control"}),
            "model": forms.TextInput(attrs={"class": "form-control"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "color": forms.TextInput(attrs={"class": "form-control"}),
            "capacity_kg": forms.NumberInput(attrs={"class": "form-control"}),
            "capacity_m3": forms.NumberInput(attrs={"class": "form-control"}),
            "fuel_type": forms.Select(attrs={"class": "form-control"}),
            "chassis_number": forms.TextInput(attrs={"class": "form-control"}),
            "renavam": forms.TextInput(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "purchase_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "purchase_value": forms.NumberInput(attrs={"class": "form-control"}),
            "current_km": forms.NumberInput(attrs={"class": "form-control"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }


class VehicleDocumentForm(forms.ModelForm):
    """Form for vehicle documents."""

    class Meta:
        model = VehicleDocument
        fields = [
            "vehicle",
            "document_type",
            "document_number",
            "issue_date",
            "expiry_date",
            "issuing_authority",
            "file",
            "notes",
        ]
        widgets = {
            "vehicle": forms.Select(attrs={"class": "form-control"}),
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


class MaintenanceRecordForm(forms.ModelForm):
    """ Form for vehicle maintenance records. """

    class Meta:
        model = MaintenanceRecord
        fields = [
            'vehicle', 'maintenance_type', 'status',
            'scheduled_date', 'completed_date',
            'odometer_reading', 'next_maintenance_km',
            'description', 'service_provider', 'cost',
            'parts_replaced', 'notes'
        ]
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-control'}),
            'maintenance_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'scheduled_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'completed_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'odometer_reading': forms.NumberInput(attrs={'class': 'form-control'}),
            'next_maintenance_km': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'service_provider': forms.TextInput(attrs={'class': 'form-control'}),
            'cost': forms.NumberInput(attrs={'class': 'form-control'}),
            'parts_replaced': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class VehicleAssignmentForm(forms.ModelForm):
    """ Form for vehicle assignment. """

    class Meta:
        model = VehicleAssignment
        fields = [
            'vehicle', 'driver', 'start_date', 'end_date',
            'is_active', 'notes'
        ]
        widgets = {
            'vehicle': forms.Select(attrs={'class': 'form-control'}),
            'driver': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter for showing only available vehicles/drivers
        if 'instance' not in kwargs or not kwargs['instance'].pk:
            self.fields['vehicle'].queryset = Vehicle.objects.filter(status='active')
            self.fields['driver'].queryset = Driver.obkects.filter(status='active')
