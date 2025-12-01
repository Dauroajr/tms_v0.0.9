from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import TenantAwareModel


class Driver(TenantAwareModel, AbstractUser):
    """
    Driver model for fleet management.
    """

    STATUS_CHOICES = [
        ("active", _("Active")),
        ("on_leave", _("On Leave")),
        ("on_duty", _("On Duty")),
        ("suspended", _("Suspended")),
        ("terminated", _("Terminated")),
    ]

    LICENSE_CATEGORY_CHOICES = [
        ("A", _("A - Motorcycle")),
        ("B", _("B - Car")),
        ("C", _("C - Truck")),
        ("D", _("D - Bus")),
        ("E", _("E - Truck with Trailer")),
    ]

    # Personal information
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    alias = models.CharField(max_length=50, blank=True, null=True)
    cpf = models.CharField(
        max_length=14,
        unique=True,
        validators=[
            RegexValidator(
                r"^\d{3}\.\d{3}\.\d{3}-\d{2}$",
                _("Enter a valid CPF (000.000.000-00 format)."),
            )
        ],
        help_text=_("CPF Number"),
    )
    birth_date = models.DateField(blank=True, null=True)
    phone_number_1 = models.CharField(max_length=15, blank=True, null=True)
    phone_number_2 = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True, unique=True)
    address = models.TextField(max_length=300, blank=True, null=True)

    # |License information
    license_number = models.CharField(max_length=30, unique=True)
    license_category = models.CharField(max_length=20, choices=LICENSE_CATEGORY_CHOICES)
    license_issue_date = models.DateField()
    license_expiry_date = models.DateField()

    # Employee Information
    hire_date = models.DateField(blank=True, null=True)
    termination_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)

    # Additional Information
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True)
    emergency_contact_phone = models.CharField(max_length=30, blank=True, null=True)
    notes = models.TextField(blank=True)

    @property
    def driver_full_name(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ["driver_full_name"]
        verbose_name = _("Driver")
        verbose_name_plural = _("Drivers")
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["cpf"]),
            models.Index(fields=["license_number"]),
        ]

    def __str__(self):
        return self.driver_full_name

    def is_available(self):
        return self.status == "active" and not self.current.assignment

    @property
    def current_assignment(self):
        return self.assignments.filter(is_active=True).first()

    def license_is_valid(self):
        return self.license_expiry_date >= timezone.now().date()

    def license_expires_soon(self):
        delta = self.license_expiry_date - timezone.now().date()
        return 0 <= delta.days <= 30


class DriverDocument(TenantAwareModel):
    """Documents related to Drivers (CNH, medical, exams, etc.)."""

    DOCUMENT_TYPE_CHOICES = [
        ("cnh", _("CNH")),
        ("aso", _("ASO (Medical Exam)")),
        ("mopp", _("MOPP Certificate")),
        ("criminal_record", _("Criminal Record")),
        ("work_permit", _("Work Permit")),
        ("other", _("Other")),
    ]

    driver = models.ForeignKey(
        Driver, on_delete=models.CASCADE, related_name="documents"
    )
    dpcument_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    document_number = models.CharField(max_length=50, blank=True, null=True)
    issue_date = models.DateField()
    expiry_date = models.DateField(blank=True, null=True)
    issuing_authority = models.CharField(max_length=150, blank=True, null=True)
    file = models.FileField(upload_to="driver_documents/", blank=True, null=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-issue_date"]
        verbose_name = _("Driver Document")
        verbose_name_plural = _("Driver Documents")
        indexes = [
            models.Index(fields=["driver", "document_type"]),
            models.Index(fields=["expiry_date"]),
        ]

    def __str__(self):
        return f"{self.driver.driver_full_name} - {self.get_document_type_display()}"

    def is_valid(self):
        """Check if document is still valid."""
        if self.expiry_date:
            return self.expiry_date >= timezone.now().date()
        return True

    def expires_soon(self, days=30):
        """Check if document expires within specified days."""
        if self.expiry_date:
            delta = self.expiry_date - timezone.now().date()
            return 0 <= delta.days <= days
        return False
