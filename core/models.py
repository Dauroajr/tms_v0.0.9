import secrets
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class TenantAwareManager(models.Manager):
    """Custom manager that automatically filters ny tenant. """
    def get_queryset(self):
        
