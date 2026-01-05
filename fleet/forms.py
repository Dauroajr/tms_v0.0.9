from django import forms
from django.utils.translation import gettext_lazy as _

from .models import (
    Vehicle,
    VehicleAssignment,
    VehicleAssignmentWorkday,
    VehicleBrand,
    VehicleDocument,
    # Employee,
    MaintenanceRecord,
)
from personnel.models import Employee


class VehicleBrandForm(forms.ModelForm):
    """Form for adding/editing vehicle brands."""

    class Meta:
        model = VehicleBrand
        fields = ["name", "country", "logo", "is_active", "notes"]
        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    # "placeholder": _("e.g., Volvo, Mercedes"),
                }
            ),
            "country": forms.TextInput(
                attrs={
                    "class": "form-control",
                    # "placeholder": _("e.g., Sweden, Germany"),
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
            "photo",
            "brand",
            "model",
            "plate",
            "type",
            "year",
            "color",
            "capacity_kg",
            "capacity_m3_or_liters",
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
            "photo": forms.FileInput(attrs={"class": "form-control"}),
            "plate": forms.TextInput(attrs={"class": "form-control"}),
            "type": forms.Select(attrs={"class": "form-control"}),
            "brand": forms.Select(attrs={"class": "form-control"}),
            "model": forms.TextInput(attrs={"class": "form-control"}),
            "year": forms.NumberInput(attrs={"class": "form-control"}),
            "color": forms.Select(attrs={"class": "form-control"}),
            "capacity_kg": forms.NumberInput(attrs={"class": "form-control"}),
            "capacity_m3_or_liters": forms.NumberInput(attrs={"class": "form-control"}),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas marcas ativas
        self.fields["brand"].queryset = VehicleBrand.objects.filter(is_active=True)


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
    """Form for vehicle maintenance records."""

    class Meta:
        model = MaintenanceRecord
        fields = [
            "vehicle",
            "maintenance_type",
            "status",
            "scheduled_date",
            "completed_date",
            "odometer_reading",
            "next_maintenance_km",
            "description",
            "service_provider",
            "cost",
            "parts_replaced",
            "notes",
        ]
        widgets = {
            "vehicle": forms.Select(attrs={"class": "form-control"}),
            "maintenance_type": forms.Select(attrs={"class": "form-control"}),
            "status": forms.Select(attrs={"class": "form-control"}),
            "scheduled_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "completed_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "odometer_reading": forms.NumberInput(attrs={"class": "form-control"}),
            "next_maintenance_km": forms.NumberInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "service_provider": forms.TextInput(attrs={"class": "form-control"}),
            "cost": forms.NumberInput(attrs={"class": "form-control"}),
            "parts_replaced": forms.Textarea(
                attrs={"class": "form-control", "rows": 2}
            ),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }


class VehicleAssignmentForm(forms.ModelForm):
    """Form for vehicle assignment with service configuration."""

    class Meta:
        model = VehicleAssignment
        fields = [
            "vehicle",
            "driver",
            "start_date",
            "end_date",
            "estimated_days",
            "workday_type",
            "daily_rate",
            "is_active",
            "notes",
        ]
        widgets = {
            "vehicle": forms.Select(attrs={"class": "form-control", "required": True}),
            "driver": forms.Select(attrs={"class": "form-control", "required": True}),
            "start_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date", "required": True}
            ),
            "end_date": forms.DateInput(
                attrs={"class": "form-control", "type": "date"}
            ),
            "estimated_days": forms.NumberInput(
                attrs={"class": "form-control", "min": "1", "value": "1"}
            ),
            "workday_type": forms.Select(
                attrs={"class": "form-control", "required": True}
            ),
            "daily_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "placeholder": "0.00",
                    "required": True,
                }
            ),
            "is_active": forms.CheckboxInput(attrs={"class": "form-check-input"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        labels = {
            "vehicle": _("Vehicle"),
            "driver": _("Driver"),
            "start_date": _("Start Date"),
            "end_date": _("End Date (optional)"),
            "estimated_days": _("Estimated Duration (days)"),
            "workday_type": _("Workday Type"),
            "daily_rate": _("Daily Rate (R$)"),
            "is_active": _("Active Assignment"),
            "notes": _("Notes"),
        }
        help_texts = {
            "vehicle": _("Select the vehicle for this assignment"),
            "driver": _("Select the driver for this assignment"),
            "estimated_days": _("Estimated number of days for this service"),
            "workday_type": _("Default workday duration (8h, 10h, 12h, or transfer)"),
            "daily_rate": _("Agreed payment value per daily (overtime = 10% per hour)"),
            "end_date": _("Leave empty for ongoing assignments"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Só filtra se for criação (instance é None ou não tem pk)
        if not self.instance or not self.instance.pk:
            # Filtros serão aplicados pela view
            pass

        # Adiciona classes de validação do Bootstrap
        for field_name, field in self.fields.items():
            if field.required:
                field.widget.attrs["required"] = True

    def clean(self):
        """Validate assignment data."""
        cleaned_data = super().clean()
        vehicle = cleaned_data.get("vehicle")
        driver = cleaned_data.get("driver")
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        is_active = cleaned_data.get("is_active", True)

        # Validate end_date is after start_date
        if start_date and end_date:
            if end_date < start_date:
                raise forms.ValidationError(_("End date cannot be before start date."))

        # Only validate conflicts for new assignments or active assignments
        if is_active and not (self.instance and self.instance.pk):
            # Check if vehicle has active assignment
            if vehicle:
                existing_vehicle = VehicleAssignment.objects.filter(
                    vehicle=vehicle, is_active=True
                ).exclude(pk=self.instance.pk if self.instance else None)

                if existing_vehicle.exists():
                    raise forms.ValidationError(
                        _("This vehicle already has an active assignment.")
                    )

            # Check if driver has active assignment
            if driver:
                existing_driver = VehicleAssignment.objects.filter(
                    driver=driver, is_active=True
                ).exclude(pk=self.instance.pk if self.instance else None)

                if existing_driver.exists():
                    raise forms.ValidationError(
                        _("This driver already has an active assignment.")
                    )

        return cleaned_data

    def clean_daily_rate(self):
        """Validate daily rate."""
        daily_rate = self.cleaned_data.get("daily_rate")
        if daily_rate and daily_rate <= 0:
            raise forms.ValidationError(_("Daily rate must be greater than zero."))
        return daily_rate

    def clean_estimated_days(self):
        """Validate estimated days."""
        estimated_days = self.cleaned_data.get("estimated_days")
        if estimated_days and estimated_days < 1:
            raise forms.ValidationError(_("Estimated days must be at least 1."))
        return estimated_days


# Adicione este form no fleet/forms.py


class VehicleAssignmentWorkdayForm(forms.ModelForm):
    """Form for registering daily workdays."""

    class Meta:
        model = VehicleAssignmentWorkday
        fields = [
            "assignment",
            "date",
            "start_time",
            "end_time",
            "break_minutes",
            "workday_type",
            "standard_hours",
            "daily_rate",
            "notes",
        ]
        widgets = {
            "assignment": forms.Select(
                attrs={"class": "form-control", "required": True}
            ),
            "date": forms.DateInput(
                attrs={"class": "form-control", "type": "date", "required": True}
            ),
            "start_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time", "required": True}
            ),
            "end_time": forms.TimeInput(
                attrs={"class": "form-control", "type": "time"}
            ),
            "break_minutes": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": "0",
                    "value": "0",
                    "placeholder": "0",
                }
            ),
            "workday_type": forms.Select(
                attrs={"class": "form-control", "required": True}
            ),
            "standard_hours": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.5",
                    "min": "0",
                    "required": True,
                }
            ),
            "daily_rate": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                    "required": True,
                }
            ),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }
        labels = {
            "assignment": _("Assignment"),
            "date": _("Work Date"),
            "start_time": _("Start Time"),
            "end_time": _("End Time"),
            "break_minutes": _("Break Time (minutes)"),
            "workday_type": _("Workday Type"),
            "standard_hours": _("Standard Hours"),
            "daily_rate": _("Daily Rate (R$)"),
            "notes": _("Notes/Observations"),
        }
        help_texts = {
            "date": _("Date of work"),
            "start_time": _("Time the work started"),
            "end_time": _("Time the work ended (leave empty if ongoing)"),
            "break_minutes": _("Total break time in minutes (optional)"),
            "workday_type": _("Type of workday (8h, 10h, 12h, or transfer)"),
            "standard_hours": _("Standard hours for this workday"),
            "daily_rate": _("Daily rate for this workday"),
            "notes": _("Any observations about this workday"),
        }

    def __init__(self, *args, **kwargs):
        # Get assignment if provided to pre-fill values
        assignment = kwargs.pop("assignment", None)
        super().__init__(*args, **kwargs)

        # If creating new workday with assignment
        if assignment and not self.instance.pk:
            # Pre-fill with assignment defaults
            self.initial["assignment"] = assignment
            self.initial["workday_type"] = assignment.workday_type
            self.initial["daily_rate"] = assignment.daily_rate

            # Set standard hours based on workday type
            if assignment.workday_type == "daily_8h":
                self.initial["standard_hours"] = 8
            elif assignment.workday_type == "daily_10h":
                self.initial["standard_hours"] = 10
            elif assignment.workday_type == "daily_12h":
                self.initial["standard_hours"] = 12

            # Lock assignment field
            self.fields["assignment"].widget.attrs["readonly"] = True
            self.fields["assignment"].disabled = True

        # Filter assignments to active ones only
        self.fields["assignment"].queryset = VehicleAssignment.objects.filter(
            is_active=True
        ).select_related("vehicle", "driver")

    def clean(self):
        """Validate workday data."""
        cleaned_data = super().clean()
        assignment = cleaned_data.get("assignment")
        date = cleaned_data.get("date")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        # Validate date is within assignment period
        if assignment and date:
            if date < assignment.start_date:
                raise forms.ValidationError(
                    _(
                        "Work date cannot be before assignment start date ({start})."
                    ).format(start=assignment.start_date)
                )

            if assignment.end_date and date > assignment.end_date:
                raise forms.ValidationError(
                    _("Work date cannot be after assignment end date ({end}).").format(
                        end=assignment.end_date
                    )
                )

            # Check for duplicate workday (only on creation)
            if not self.instance.pk and assignment.workdays.filter(date=date).exists():
                raise forms.ValidationError(
                    _("A workday already exists for this date.")
                )

        # Validate end_time > start_time (if end_time is set)
        if start_time and end_time:
            # Note: overnight shifts are allowed, handled in model
            pass

        return cleaned_data

    def save(self, commit=True):
        """Save workday and recalculate assignment totals."""
        workday = super().save(commit=False)

        if commit:
            workday.save()
            # Recalculate assignment totals
            workday.assignment.calculate_totals()

        return workday
