from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from core.models import TenantAwareModel


class Employee(TenantAwareModel, AbstractUser):
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
        max_length=30,
        choices=EMPLOYEE_TYPE_CHOICES,
        help_text=_("Type of Employee"),
        verbose_name=_("Type of Employee"),
    )
    first_name = models.CharField(max_length=30, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=30, verbose_name=_("Last Name"))
    alias = models.CharField(
        max_length=50, blank=True, null=True, verbose_name=_("Alias")
    )
    cpf = models.CharField(
        max_length=14,
        unique=True,
        validators=[
            RegexValidator(
                r"^\d{3}\.\d{3}\.\d{3}-\d{2}$",
                _("Enter a valid CPF (000.000.000-00 format)"),
            )
        ],
        help_text=_("CPF Number"),
        verbose_name=_("CPF"),
    )
    rg = models.CharField(
        max_length=25,
        blank=True,
        help_text=_("RG (Identity Card Number)"),
        verbose_name=_("Identification Number"),
    )
    birth_date = models.DateField(
        blank=True, null=True, verbose_name=_("Date of Birth")
    )
    gender = models.CharField(
        max_length=20,
        choices=[
            ("male", _("Male")),
            ("female", _("Female")),
            ("other", _("Other")),
        ],
        blank=True,
        null=True,
        verbose_name=_("Gender"),
    )

    # Contact Information
    phone_number_1 = models.CharField(
        max_length=15, blank=True, null=True, verbose_name=_("Phone Number 1")
    )
    phone_number_2 = models.CharField(
        max_length=15, blank=True, null=True, verbose_name=_("Phone Number 2")
    )
    email = models.EmailField(blank=True, verbose_name=_("E-mail"))
    address = models.TextField(verbose_name=_("Address"))
    city = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("City")
    )
    state = models.CharField(
        max_length=100, blank=True, null=True, verbose_name=_("State")
    )
    zip_code = models.CharField(max_length=10, blank=True, verbose_name=_("Zip Code"))

    # Employment Information
    employee_number = models.CharField(
        max_length=30,
        unique=True,
        help_text=_("Employee Number"),
        verbose_name=_("Employee Identification Number"),
    )
    hire_date = models.DateField(blank=True, verbose_name=_("Hire Date"))
    termination_date = models.DateField(
        blank=True, null=True, verbose_name=_("Termination Date")
    )
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default="active",
        verbose_name=_("Status"),
    )

    # Financial Information
    salary = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
        help_text=_("Salary Amount"),
        verbose_name=_("Salary"),
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
        verbose_name=_("Payment Cycle"),
    )

    payment_method = models.CharField(
        max_length=30,
        choices=[
            ("bank_transfer_ted", _("Bank Transfer - TED")),
            ("pix", _("PIX")),
            ("cash", _("Cash")),
            ("check", _("Check")),
        ],
    )

    bank_name = models.CharField(
        max_length=100, blank=True, verbose_name=_("Bank Name")
    )
    bank_branch = models.CharField(
        max_length=100, blank=True, verbose_name=_("Bank Branch")
    )
    bank_account = models.CharField(
        max_length=100, blank=True, verbose_name=_("Bank Account")
    )

    # Emergency Contact
    emergency_contact_name = models.CharField(
        max_length=200, blank=True, verbose_name=_("Emergency Contact Name")
    )
    emergency_contact_relationship = models.CharField(
        max_length=50, blank=True, verbose_name=_("Emergency Contact Relationship")
    )
    emergency_contact_phone = models.CharField(
        max_length=20, blank=True, verbose_name=_("Emergency Contact Phone")
    )

    # Additional Information
    photo = models.ImageField(
        upload_to="employee_photos/", blank=True, null=True, verbose_name=_("Photo")
    )
    notes = models.TextField(blank=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    class Meta:
        ordering = ["full_name"]
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "employee_type"]),
            models.Index(fields=["cpf"]),
            models.Index(fields=["employee_number"]),
        ]

    def str(self):
        return self.full_name

    def is_active(self):
        return self.status == "active"

    def get_age(self):
        # Calculate employee's age
        today = timezone.now().date()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )

    def get_tenure_years(self):
        # Calculate years of service
        if self.termination_date:
            end_date = self.termination_date
        else:
            end_date = timezone.now().date()

        years = end_date.year - self.hire_date.year
        if (end_date.month, end_date.day) < (self.hire_date.month, self.hire_date.day):
            years -= 1
        return years

    def has_driver_profile(self):
        # Check if employee has a driver profile
        return hasattr(self, "driver_profile")

    def has_security_profile(self):
        return hasattr(self, "security_profile")


class DriverProfile(TenantAwareModel):
    """
    Driver-specific information profile.
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
        ("AB", _("AB - Motorcycle and Car")),
        ("AC", _("AC - Motorcycle and Truck")),
        ("AD", _("AD - Motorcycle and Bus")),
        ("AE", _("AE - Motorcycle and Truck with Trailer")),
    ]

    employee = models.OneToOneField(
        Employee,
        on_delete=models.CASCADE,
        related_name="driver_profile",
        limit_choices_to={"employee_type": "driver"},
        verbose_name=_("Driver"),
    )

    # Personal information
    """ first_name = models.CharField(max_length=30, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=30, verbose_name=_("Last Name"))
    alias = models.CharField(max_length=50, blank=True, null=True, verbose_name=_("Alias"))
    cpf = models.CharField(
        max_length=14,
        unique=True,
        validators=[
            RegexValidator(
                r"^\d{3}\.\d{3}\.\d{3}-\d{2}$",  # noqa
                _("Enter a valid CPF (000.000.000-00 format)."),
            )
        ],
        help_text=_("CPF Number"),
        verbose_name=_("CPF")
    )
    birth_date = models.DateField(blank=True, null=True, verbose_name=_("Date of Birth"))
    phone_number_1 = models.CharField(max_length=15, blank=True, null=True, verbose_name=_("First Name"))
    phone_number_2 = models.CharField(max_length=15, blank=True, null=True, verbose_name=_("Last Name"))
    email = models.EmailField(blank=True, null=True, unique=True, verbose_name=_("E-mail"))
    address = models.TextField(max_length=300, blank=True, null=True, verbose_name=_("Address")) """

    # License information
    license_number = models.CharField(
        max_length=30, unique=True, verbose_name=_("License Number")
    )
    license_category = models.CharField(
        max_length=20,
        choices=LICENSE_CATEGORY_CHOICES,
        verbose_name=_("License Category"),
    )
    license_issue_date = models.DateField(verbose_name=_("License Issue Date"))
    license_expiry_date = models.DateField(verbose_name=_("License Expiry Date"))
    license_first_issue_date = models.DateField(verbose_name=_("Date of 1st CNH Issue"))

    # Driver Qualifications
    has_mopp = models.BooleanField(
        default=False,
        help_text=_("Has MOPP Certification (hazardous materials transport)"),
        verbose_name=_("Has MOPP Certification"),
    )
    mopp_expiry_date = models.DateField(
        blank=True, null=True, verbose_name=_("MOPP Expiry Date)")
    )

    has_defensive_driving = models.BooleanField(
        default=False,
        help_text=_("Has Defensive Driving Course Certification"),
        verbose_name=_("Has Defensive Driving Certificate"),
    )

    # Medical Information
    last_medical_exam_date = models.DateField(
        blank=True, null=True, verbose_name=_("Last Medical Exam Date")
    )

    next_medical_exam_date = models.DateField(
        blank=True, null=True, verbose_name=_("Next Medical Exam Date")
    )
    blood_type = models.CharField(
        max_length=5,
        choices=[
            ("A+", ("A+")),
            ("A-", ("A-")),
            ("B+", ("B+")),
            ("B-", ("B-")),
            ("AB+", ("AB+")),
            ("AB-", ("AB-")),
            ("O+", ("O+")),
            ("O-", ("O-")),
        ],
        blank=True,
        verbose_name=_("Blood Type"),
    )

    # Performance Tracking
    total_trips = models.PositiveIntegerField(default=0, verbose_name=_("Total Trips"))
    total_km_driven = models.PositiveIntegerField(
        default=0, verbose_name=_("Total km Driven")
    )
    accidents_count = models.PositiveIntegerField(
        default=0, verbose_name=_("Accidents Count")
    )
    violations_count = models.PositiveIntegerField(
        default=0, verbose_name=_("Violation Count")
    )

    notes = models.TextField(blank=True, verbose_name=_("Notes"))

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
        return self.license_expiry_date >= timezone.now().date()

    def license_expires_soon(self, days=30):
        delta = self.license_expiry_date - timezone.now().date()
        return 0 <= delta.days <= days

    def medical_exam_is_valid(self):
        if self.next_medical_exam_date:
            return self.next_medical_exam_date >= timezone.now().date()
        return False

    def medical_exam_expires_soon(self, days=30):
        if self.next_medical_exam_date:
            delta = self.next_medical_exam_date - timezone.now().date()
            return 0 <= delta.days <= days
        return False

    def is_availaboe_for_assignment(self):
        return (
            self.employee.status == "active"
            and self.license_is_valid()
            and self.medical_exam_is_valid()
            and not hasattr(self, "current_assignment")
        )

    # Employee Information
    """ hire_date = models.DateField(blank=True, null=True, verbose_name=_("Hire Date"))
    termination_date = models.DateField(blank=True, null=True, verbose_name=_("Termination Date"))
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active", verbose_name=_("Status"))
    salary = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, verbose_name=_("Salary"))

    # Additional Information
    emergency_contact_name = models.CharField(max_length=100, blank=True, null=True, verbose_name=_("Emergency Contact Name"))
    emergency_contact_phone = models.CharField(max_length=30, blank=True, null=True, verbose_name=_("Emergency Contact Phone"))
    notes = models.TextField(blank=True, verbose_name=_("Notes")) """

    @property
    def driver_full_name(self):
        return f"{self.first_name} {self.last_name}"

    """ class Meta:
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
        return 0 <= delta.days <= 30 """


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
        return self.security_license_expiry_date >= timezone.now().date()

    def license_expires_soon(self, days=30):
        """Check if license expires within specified days."""
        delta = self.security_license_expiry_date - timezone.now().date()
        return 0 <= delta.days <= days

    def needs_recycling_course(self):
        """Check if needs recycling course."""
        if self.next_recycling_date:
            return self.next_recycling_date <= timezone.now().date()
        return True

    def firearms_license_is_valid(self):
        """Check if firearms license is valid."""
        if self.has_firearms_license and self.firearms_license_expiry:
            return self.firearms_license_expiry >= timezone.now().date()
        return not self.has_firearms_license


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
