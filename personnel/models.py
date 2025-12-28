# from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from core.models import TenantAwareModel


class Employee(TenantAwareModel):
    """Base employee model for all personnel types."""

    EMPLOYEE_TYPE_CHOICES = [
        ("driver", _("Driver")),
        ("security", _("Security Guard")),
        ("mechanic", _("Mechanic")),
        ("admin", _("Administrative")),
        ("helper", _("Helper")),
        ("other", _("Other")),
    ]

    STATUS_CHOICES = [
        ("active", _("Active")),
        ("on_leave", _("On Leave")),
        ("vacation", _("Vacation")),
        ("suspended", _("Suspended")),
        ("terminated", _("Terminated")),
    ]

    # Personal Information
    employee_type = models.CharField(
        max_length=20, choices=EMPLOYEE_TYPE_CHOICES, help_text=_("Type of employee")
    )
    full_name = models.CharField(max_length=200)
    cpf = models.CharField(
        max_length=14,
        unique=True,
        validators=[
            RegexValidator(
                r"^\d{3}\.\d{3}\.\d{3}-\d{2}$", "Enter a valid CPF (000.000.000-00)"
            )
        ],
        help_text=_("CPF number"),
    )
    rg = models.CharField(max_length=20, blank=True, help_text=_("RG (Identity card)"))
    birth_date = models.DateField(verbose_name=_('Date of Birth'))
    gender = models.CharField(
        max_length=10,
        choices=[
            ("male", _("Male")),
            ("female", _("Female")),
            ("other", _("Other")),
        ],
        blank=True,
    )

    # Contact Information
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    address = models.TextField()
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=2, blank=True)
    zip_code = models.CharField(max_length=10, blank=True)

    # Employment Information
    employee_number = models.CharField(
        max_length=20, unique=True, help_text=_("Internal employee ID/number")
    )
    hire_date = models.DateField()
    termination_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # Financial Information
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Monthly salary"),
    )
    payment_cycle = models.CharField(
        max_length=20,
        choices=[
            ("monthly", _("Monthly")),
            ("hourly", _("Hourly")),
            ("daily", _("Daily")),
            ("commission", _("Commission")),
        ],
        default="monthly",
        blank=True,
        null=True,
    )
    payment_method = models.CharField(
        max_length=20,
        choices=[
            ("bank_transfer", _("Bank Transfer")),
            ('cash', _('Cash')),
            ('check', _('Check')),
            ('other', _('Other'))
        ],
        default="bank_transfer",
        verbose_name=_("Payment Method"),
        blank=True,
        null=True,
    )
    bank_name = models.CharField(max_length=100, blank=True)
    bank_branch = models.CharField(max_length=10, blank=True)
    bank_account = models.CharField(max_length=20, blank=True)

    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=200, blank=True)
    emergency_contact_relationship = models.CharField(max_length=50, blank=True)
    emergency_contact_phone = models.CharField(max_length=20, blank=True)

    # Additional Information
    photo = models.ImageField(
        upload_to="personnel/photos/",
        blank=True,
        null=True,
        help_text=_("Employee photo"),
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["full_name"]
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "employee_type"]),
            models.Index(fields=["cpf"]),
            models.Index(fields=["employee_number"]),
            models.Index(fields=["full_name"]),  # Adicionado para ordering
        ]

    def __str__(self):
        return f"{self.full_name} ({self.employee_number})"

    def is_active(self):
        """Check if employee is active."""
        return self.status == "active"

    def get_age(self):
        """Calculate employee's age."""
        today = timezone.now().date()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )

    def get_tenure_years(self):
        """Calculate years of service."""
        if self.termination_date:
            end_date = self.termination_date
        else:
            end_date = timezone.now().date()

        years = end_date.year - self.hire_date.year
        if (end_date.month, end_date.day) < (self.hire_date.month, self.hire_date.day):
            years -= 1
        return years

    def has_driver_profile(self):
        """Check if employee has a driver profile."""
        return hasattr(self, "driver_profile")

    def has_security_profile(self):
        """Check if employee has a security profile."""
        return hasattr(self, "security_profile")


class DriverProfile(TenantAwareModel):
    """Driver-specific information profile."""

    LICENSE_CATEGORY_CHOICES = [
        ("A", "A - Motorcycle"),
        ("B", "B - Car"),
        ("C", "C - Truck"),
        ("D", "D - Bus"),
        ("E", "E - Truck with Trailer"),
        ("AB", "AB - Motorcycle and Car"),
        ("AC", "AC - Motorcycle and Truck"),
        ("AD", "AD - Motorcycle and Bus"),
        ("AE", "AE - Motorcycle and Truck with Trailer"),
    ]

    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name="driver_profile",
        limit_choices_to={"employee_type": "driver"},
    )

    # License Information
    license_number = models.CharField(
        max_length=20, unique=True, help_text=_("CNH number")
    )
    license_category = models.CharField(max_length=5, choices=LICENSE_CATEGORY_CHOICES)
    license_issue_date = models.DateField()
    license_expiry_date = models.DateField()
    license_first_issue_date = models.DateField(
        blank=True, null=True, help_text=_("Date of first CNH issue")
    )

    # Driver Qualifications
    has_mopp = models.BooleanField(
        default=False, help_text=_("Has MOPP certification (hazardous materials)")
    )
    mopp_expiry_date = models.DateField(blank=True, null=True)

    has_defensive_driving = models.BooleanField(
        default=False, help_text=_("Has defensive driving course")
    )
    defensive_driving_date = models.DateField(blank=True, null=True)

    # Medical Information
    last_medical_exam_date = models.DateField(blank=True, null=True)
    next_medical_exam_date = models.DateField(blank=True, null=True)
    blood_type = models.CharField(
        max_length=5,
        choices=[
            ("A+", "A+"),
            ("A-", "A-"),
            ("B+", "B+"),
            ("B-", "B-"),
            ("AB+", "AB+"),
            ("AB-", "AB-"),
            ("O+", "O+"),
            ("O-", "O-"),
        ],
        blank=True,
    )

    # Performance Tracking
    total_trips = models.PositiveIntegerField(default=0)
    total_km_driven = models.PositiveIntegerField(default=0)
    accidents_count = models.PositiveIntegerField(default=0)
    violations_count = models.PositiveIntegerField(default=0)

    # Additional Information
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Driver Profile")
        verbose_name_plural = _("Driver Profiles")
        indexes = [
            models.Index(fields=["license_number"]),
            models.Index(fields=["license_expiry_date"]),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - CNH: {self.license_number}"

    def license_is_valid(self):
        """Check if driver's license is still valid."""
        if not self.license_expiry_date:
            return False
        return self.license_expiry_date >= timezone.now().date()

    def license_expires_soon(self, days=30):
        """Check if license expires within specified days."""
        if not self.license_expiry_date:
            return False
        delta = self.license_expiry_date - timezone.now().date()
        return 0 <= delta.days <= days

    def medical_exam_is_valid(self):
        """Check if medical exam is still valid."""
        if not self.next_medical_exam_date:
            return False
        return self.next_medical_exam_date >= timezone.now().date()

    def medical_exam_expires_soon(self, days=30):
        """Check if medical exam expires soon."""
        if not self.next_medical_exam_date:
            return False
        delta = self.next_medical_exam_date - timezone.now().date()
        return 0 <= delta.days <= days

    def is_available_for_assignment(self):
        """Check if driver is available for vehicle assignment."""
        return (
            self.employee.status == "active"
            and self.license_is_valid()
            and self.medical_exam_is_valid()
            and not hasattr(self, "current_assignment")
        )


class SecurityProfile(TenantAwareModel):
    """Security guard-specific information profile."""

    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name="security_profile",
        limit_choices_to={"employee_type": "security"},
    )

    # Security License
    security_license_number = models.CharField(
        max_length=20, unique=True, help_text=_("Security guard license number")
    )
    security_license_issue_date = models.DateField()
    security_license_expiry_date = models.DateField()

    # Certifications
    has_firearms_license = models.BooleanField(
        default=False, help_text=_("Has firearms license")
    )
    firearms_license_number = models.CharField(max_length=20, blank=True)
    firearms_license_expiry = models.DateField(blank=True, null=True)

    has_vigilant_course = models.BooleanField(
        default=False, help_text=_("Has vigilant security course")
    )
    vigilant_course_date = models.DateField(blank=True, null=True)

    has_recycling_course = models.BooleanField(
        default=False,
        help_text=_("Has security recycling course (required every 2 years)"),
    )
    recycling_course_date = models.DateField(blank=True, null=True)
    next_recycling_date = models.DateField(blank=True, null=True)

    # Medical Information
    last_medical_exam_date = models.DateField(blank=True, null=True)
    next_medical_exam_date = models.DateField(blank=True, null=True)

    # Performance Tracking
    shifts_worked = models.PositiveIntegerField(default=0)
    incidents_reported = models.PositiveIntegerField(default=0)

    # Additional Information
    specializations = models.TextField(
        blank=True,
        help_text=_(
            "Security specializations (e.g., personal security, event security)"
        ),
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = _("Security Profile")
        verbose_name_plural = _("Security Profiles")
        indexes = [
            models.Index(fields=["security_license_number"]),
            models.Index(fields=["security_license_expiry_date"]),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - Security License: {self.security_license_number}"

    def license_is_valid(self):
        """Check if security license is still valid."""
        if not self.security_license_expiry_date:
            return False
        return self.security_license_expiry_date >= timezone.now().date()

    def license_expires_soon(self, days=30):
        """Check if license expires within specified days."""
        if not self.security_license_expiry_date:
            return False
        delta = self.security_license_expiry_date - timezone.now().date()
        return 0 <= delta.days <= days

    def needs_recycling_course(self):
        """Check if needs recycling course."""
        if not self.next_recycling_date:
            return True  # Se não tem data agendada, precisa fazer
        return self.next_recycling_date <= timezone.now().date()

    def firearms_license_is_valid(self):
        """Check if firearms license is valid."""
        if not self.has_firearms_license:
            return True  # Não tem arma = não precisa licença válida
        if not self.firearms_license_expiry:
            return False  # Tem arma mas sem validade = inválido
        return self.firearms_license_expiry >= timezone.now().date()


class EmployeeDocument(TenantAwareModel):
    """Documents related to employees (all types)."""

    DOCUMENT_TYPE_CHOICES = [
        # Common Documents
        ("rg", _("RG (Identity Card)")),
        ("cpf", _("CPF")),
        ("ctps", _("CTPS (Work Card)")),
        ("voter_id", _("Voter Registration")),
        ("military_id", _("Military ID")),
        ("birth_cert", _("Birth Certificate")),
        ("marriage_cert", _("Marriage Certificate")),
        # Driver Documents
        ("cnh", _("CNH (Driver License)")),
        ("aso", _("ASO (Medical Exam)")),
        ("mopp", _("MOPP Certificate")),
        ("defensive_driving", _("Defensive Driving Certificate")),
        # Security Documents
        ("security_license", _("Security Guard License")),
        ("firearms_license", _("Firearms License")),
        ("vigilant_course", _("Vigilant Course Certificate")),
        ("recycling_course", _("Recycling Course Certificate")),
        # Work Documents
        ("contract", _("Work Contract")),
        ("termination", _("Termination Letter")),
        ("reference", _("Reference Letter")),
        ("criminal_record", _("Criminal Record")),
        # Other
        ("photo", _("Photo")),
        ("other", _("Other")),
    ]

    employee = models.ForeignKey(
        Employee, on_delete=models.CASCADE, related_name="documents"
    )
    document_type = models.CharField(max_length=30, choices=DOCUMENT_TYPE_CHOICES)
    document_number = models.CharField(max_length=50, blank=True)
    issue_date = models.DateField()
    expiry_date = models.DateField(
        blank=True, null=True, help_text=_("Leave blank if document does not expire")
    )
    issuing_authority = models.CharField(max_length=100, blank=True)
    file = models.FileField(
        upload_to="personnel/employee_documents/", blank=True, null=True
    )
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-issue_date"]
        verbose_name = _("Employee Document")
        verbose_name_plural = _("Employee Documents")
        indexes = [
            models.Index(fields=["employee", "document_type"]),
            models.Index(fields=["expiry_date"]),
        ]

    def __str__(self):
        return f"{self.employee.full_name} - {self.get_document_type_display()}"

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
