from django.core.validators import RegexValidator
from django.db import models
from django.utils.html import format_html
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import TenantAwareModel
from personnel.models import Employee


class VehicleBrand(TenantAwareModel):
    """Vehicle brand/manufacturer model."""

    BRAND_CHOICES = [
        # Carros
        ("alfa_romeo", "Alfa Romeo"),
        ("aston_martin", "Aston Martin"),
        ("audi", "Audi"),
        ("bentley", "Bentley"),
        ("bmw", "BMW"),
        ("bugatti", "Bugatti"),
        ("byd", "BYD"),
        ("chery", "Chery"),
        ("chevrolet", "Chevrolet"),
        ("citroen", "Citroën"),
        ("dacia", "Dacia"),
        ("ferrari", "Ferrari"),
        ("fiat", "Fiat"),
        ("ford", "Ford"),
        ("geely", "Geely"),
        ("great_wall", "Great Wall"),
        ("honda", "Honda"),
        ("hyundai", "Hyundai"),
        ("jaguar", "Jaguar"),
        ("kia", "Kia"),
        ("lamborghini", "Lamborghini"),
        ("land_rover", "Land Rover"),
        ("maserati", "Maserati"),
        ("mazda", "Mazda"),
        ("mercedes_benz", "Mercedes-Benz"),
        ("mitsubishi", "Mitsubishi"),
        ("nissan", "Nissan"),
        ("peugeot", "Peugeot"),
        ("porsche", "Porsche"),
        ("renault", "Renault"),
        ("rolls_royce", "Rolls-Royce"),
        ("saab", "Saab"),
        ("seat", "SEAT"),
        ("skoda", "Škoda"),
        ("subaru", "Subaru"),
        ("suzuki", "Suzuki"),
        ("tesla", "Tesla"),
        ("toyota", "Toyota"),
        ("volkswagen", "Volkswagen"),
        ("volvo", "Volvo"),

        # Caminhões e ônibus
        ("ashok_leyland", "Ashok Leyland"),
        ("caio", "Caio"),
        ("daf", "DAF"),
        ("freightliner", "Freightliner"),
        ("hino", "Hino"),
        ("international", "International"),
        ("iveco", "Iveco"),
        ("kenworth", "Kenworth"),
        ("mack", "Mack"),
        ("man", "MAN"),
        ("marcopolo", "Marcopolo"),
        ("mercedes_trucks", "Mercedes-Benz Trucks"),
        ("neobus", "Neobus"),
        ("peterbilt", "Peterbilt"),
        ("scania", "Scania"),
        ("tata", "Tata Motors"),
        ("volvo_trucks", "Volvo Trucks"),
        ("yutong", "Yutong"),

        # Motocicletas
        ("aprilia", "Aprilia"),
        ("bajaj", "Bajaj"),
        ("ducati", "Ducati"),
        ("harley_davidson", "Harley-Davidson"),
        ("honda_moto", "Honda (Motos)"),
        ("kawasaki", "Kawasaki"),
        ("ktm", "KTM"),
        ("mv_agusta", "MV Agusta"),
        ("piaggio", "Piaggio"),
        ("royal_enfield", "Royal Enfield"),
        ("suzuki_moto", "Suzuki (Motos)"),
        ("triumph", "Triumph"),
        ("vespa", "Vespa"),
        ("yamaha", "Yamaha"),
    ]

    def logo_path(obj, instance):
        if instance.logo:
            return format_html(obj and f"<src={obj.logo.url} height='40' width='40' />")

    name = models.CharField(
        max_length=100,
        choices=BRAND_CHOICES,
        help_text=_("Brand name (e.g., Jeep, Mercedes)"),
    )
    country = models.CharField(
        max_length=50, blank=True, help_text=_("Country of origin")
    )
    logo = models.ImageField(upload_to="fleet/logos/brands", blank=True, null=True)
    is_active = models.BooleanField(default=True, help_text=_("Is this brand active?"))
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["name"]
        verbose_name = _("Vehicle Brand")
        verbose_name_plural = _("Vehicle Brands")
        unique_together = ["tenant", "name"]
        indexes = [
            models.Index(fields=["tenant", "name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return self.name

    def get_vehicles_count(self):
        return self.vehicles.filter(status="active").count()


class Vehicle(TenantAwareModel):
    """Vehicle model for fleet management."""

    TYPE_CHOICES = [
        ("truck", _("Truck")),
        ("van", _("Van")),
        ("trailer", _("Trailer")),
        ("semi_trailer", _("Semi Trailer")),
        ("pickup", _("Pickup")),
        ("motorcycle", _("Motorcycle")),
        ("SUV", _("SUV")),
        ("minivan", _("Minivan")),
        ("sedan", _("Sedan")),
        ("other", _("Other")),
    ]

    STATUS_CHOICES = [
        ("active", _("Active")),
        ("maintenance", _("In Maintenance")),
        ("inactive", _("Inactive")),
        ("available", _("Available")),
        ("unavailable", _("Unavailable")),
        ("sold", _("Sold")),
    ]

    FUEL_CHOICES = [
        ("diesel", _("Diesel")),
        ("gasoline", _("Gasoline")),
        ("ethanol", _("Ethanol")),
        ("flex", _("Flex")),
        ("electric", _("Electric")),
        ("hybrid", _("Hybrid")),
    ]

    COLOR_CHOICES = [
        ("black", _("Black")),
        ("blue", _("Blue")),
        ("brown", _("Brown")),
        ("carbon", _("Carbon")),
        ("darkblue", _("Dark Blue")),
        ("darkgreen", _("Dark Green")),
        ("gold", _("Gold")),
        ("grafite", _("Grafite")),
        ("green", _("Green")),
        ("grey", _("Grey")),
        ("indigo", _("Indigo")),
        ("maroon", _("Maroon")),
        ("orange", _("Orange")),
        ("pink", _("Pink")),
        ("purple", _("Purple")),
        ("red", _("Red")),
        ("silver", _("Silver")),
        ("violet", _("Violet")),
        ("white", _("White")),
        ("yellow", _("Yellow")),
        ("other", _("Other")),
    ]

    type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=None)
    brand = models.ForeignKey(VehicleBrand, on_delete=models.PROTECT)
    model = models.CharField(max_length=100, help_text=_("Vehicle Model"))
    plate = models.CharField(
        max_length=10,
        unique=True,
        validators=[
            RegexValidator(
                r"^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$",
                _("Enter a valid plate (ABC1D23 format)."),
            )
        ],
        help_text=_("Vehicle plate (e.g ABC1D23)"),
    )
    year = models.PositiveIntegerField(help_text=_("Manufacturing Year"))
    color = models.CharField(max_length=30, choices=COLOR_CHOICES, blank=True)

    capacity_kg = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Load capacity in kilograms"),
    )

    capacity_m3 = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Volume capacity in cubic meters"),
    )

    fuel_type = models.CharField(
        max_length=20,
        choices=FUEL_CHOICES,
        default="diesel",
    )

    chassis_number = models.CharField(
        max_length=50, unique=True, verbose_name=_("Chassis Number")
    )
    renavam = models.CharField(
        max_length=11, unique=True, help_text=_("RENAVAM number")
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    purchase_date = models.DateField(blank=True, null=True)
    purchase_value = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )

    current_km = models.PositiveIntegerField(
        default=0, help_text=_("Current odometer reading")
    )
    last_maintenance_km = models.PositiveIntegerField(default=0, blank=True, null=True)
    next_maintenance_km = models.PositiveIntegerField(blank=True, null=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["plate"]
        verbose_name = _("Vehicle")
        verbose_name_plural = _("Vehicles")
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["plate"]),
        ]

    def __str__(self):
        return f"{self.brand} {self.model} - {self.plate}"

    def is_available(self):
        """Check if vehicle is available for assignment."""
        return self.status == "active" and not self.current_assignment

    @property
    def current_assignment(self):
        """Get current vehicle assignment."""
        return self.assignments.filter(is_active=True).first()

    def needs_maintenance(self):
        """Check if vehicle needs maintenance based on km."""
        if self.next_maintenance_km:
            return self.current_km >= self.next_maintenance_km
        return False


class VehicleDocument(TenantAwareModel):
    """Documents related to vehicles(CRLV, insurance, etc.)."""

    DOCUMENT_TYPE_CHOICES = [
        ("crlv", _("CRLV (Vehicle Registration)")),
        ("insurance", _("Insurance")),
        ("antt", _("ANTT Registration")),
        ("inspection", _("Vehicle Inspection")),
        ("emission", _("Emission Certificate")),
        ("other", _("Other")),
    ]

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPE_CHOICES)
    document_number = models.CharField(max_length=50, blank=True)
    issue_date = models.DateField(verbose_name=_("Issue Date"))
    expiry_date = models.DateField(blank=True, null=True)
    issuing_authority = models.CharField(max_length=100, blank=True)
    file = models.FileField(
        upload_to="fleet/vehicle_documents/",
        blank=True,
        null=True,
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-issue_date"]
        verbose_name = _("Vehicle Document")
        verbose_name_plural = _("Vehicle Documents")
        indexes = [
            models.Index(fields=["vehicle", "document_type"]),
            models.Index(fields=["expiry_date"]),
        ]

    def __str__(self):
        return f"{self.vehicle.plate} - {self.get_document_type_display()}"

    def is_valid(self):
        """Check if document is still valid."""
        if self.expiry_date:
            return self.expiry_date >= timezone.now().date()
        return True

    def expires_soon(self, days=30):
        """Check if document expires within given days."""
        if self.expiry_date:
            delta = self.expiry_date - timezone.now().date()
            return 0 <= delta <= days
        return False


class MaintenanceRecord(TenantAwareModel):
    """Maintenance records for vehicles."""

    MAINTENANCE_TYPE_CHOICES = [
        ("preventive", _("Preventive Maintenance")),
        ("corrective", _("Corrective Maintenance")),
        ("inspection", _("Inspection")),
        ("tire_change", _("Tire Change")),
        ("oil_change", _("Oil Change")),
        ("brake_service", _("Brake Service")),
        ("other", _("Other")),
    ]

    STATUS_CHOICES = [
        ("scheduled", _("Scheduled")),
        ("in_progress", _("In Progress")),
        ("completed", _("Completed")),
        ("cancelled", _("Cancelled")),
    ]

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="maintenance_records"
    )

    maintenance_type = models.CharField(
        max_length=30,
        choices=MAINTENANCE_TYPE_CHOICES,
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="scheduled",
    )

    scheduled_date = models.DateTimeField()
    completed_date = models.DateTimeField()

    odometer_reading = models.PositiveIntegerField(
        help_text=_("odometer km at maintenance.")
    )
    next_maintenance_km = models.PositiveIntegerField(blank=True, null=True)

    description = models.TextField()
    service_provider = models.CharField(max_length=250, blank=True)
    cost = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
    )

    parts_replaced = models.TextField(
        blank=True, help_text=_("List of parts replaced.")
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-scheduled_date"]
        verbose_name = _("Maintenance Record")
        verbose_name_plural = _("Maintenance Records")
        indexes = [
            models.Index(fields=["vehicle", "status"]),
            models.Index(fields=["scheduled_date"]),
        ]

    def __str__(self):
        return f"{self.vehicle.plate} - {self.get_maintenance_type_display()} - {self.scheduled_date}"

    def mark_completed(self, completed_date=None):
        """Mark maintenance as completed."""

        self.status = "completed"
        self.completed_date = completed_date or timezone.now().date()
        self.save()

        # Update vehicle's last maintenance km
        if self.odometer_reading > self.vehicle.last_maintenance_km:
            self.vehicle.last_maintenance_km = self.odometer_reading
            if self.next_maintenance_km:
                self.vehicle.next_maintenance_km = self.netx_maintenance_km
            self.vehicle.save()


class VehicleAssignment(TenantAwareModel):
    """Assignment of drivers to vehicles."""

    vehicle = models.ForeignKey(
        Vehicle, on_delete=models.CASCADE, related_name="assignments"
    )

    # MUDANÇA: Agora referencia Employee ao invés de Driver
    driver = models.ForeignKey(
        "personnel.Employee",  # FK para personnel.Employee
        on_delete=models.CASCADE,
        related_name="vehicle_assignments",
        limit_choices_to={"employee_type": "driver"},  # Só motoristas
    )

    start_date = models.DateField(default=timezone.now)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-start_date"]
        verbose_name = _("Vehicle Assignment")
        verbose_name_plural = _("Vehicle Assignments")
        indexes = [
            models.Index(fields=["vehicle", "is_active"]),
            models.Index(fields=["driver", "is_active"]),
        ]

    def __str__(self):
        return f"{self.driver.full_name} → {self.vehicle.plate}"

    def clean(self):
        """Validate that employee is a driver with valid license."""
        super().clean()

        from django.core.exceptions import ValidationError

        # Check if employee is a driver
        if self.driver.employee_type != "driver":
            raise ValidationError(
                'Only employees with type "driver" can be assigned to vehicles.'
            )

        # Check if driver has profile
        if not self.driver.has_driver_profile():
            raise ValidationError("This driver does not have a driver profile.")

        # Check if driver's license is valid
        driver_profile = self.driver.driver_profile
        if not driver_profile.license_is_valid():
            raise ValidationError("This driver's license is expired.")

        # Check if driver's medical exam is valid
        if not driver_profile.medical_exam_is_valid():
            raise ValidationError("This driver's medical exam is expired.")

    def save(self, *args, **kwargs):
        """Override save to ensure only one active assignment per vehicle/driver."""
        if self.is_active:
            # Deactivate other active assignments for this vehicle
            VehicleAssignment.objects.filter(
                vehicle=self.vehicle, is_active=True
            ).exclude(id=self.id).update(
                is_active=False, end_date=timezone.now().date()
            )

            # Deactivate other active assignments for this driver
            VehicleAssignment.objects.filter(
                driver=self.driver, is_active=True
            ).exclude(id=self.id).update(
                is_active=False, end_date=timezone.now().date()
            )

        super().save(*args, **kwargs)

    def end_assignment(self, end_date=None):
        """End this assignment."""
        self.is_active = False
        self.end_date = end_date or timezone.now().date()
        self.save()
