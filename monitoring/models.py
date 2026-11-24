from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class Device(models.Model):
    name = models.CharField(max_length=80)
    serial = models.CharField(max_length=40, unique=True)
    tags = models.ManyToManyField(Tag, related_name="devices", blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="devices",
        null=True,
        blank=True,
    )

    def __str__(self):
        return f"{self.name} ({self.serial})"


class Passport(models.Model):
    device = models.OneToOneField(
        Device, on_delete=models.CASCADE, related_name="passport"
    )
    location = models.CharField(max_length=120)

    def __str__(self):
        return f"Паспорт: {self.device.serial} ({self.location})"


class Measurement(models.Model):
    device = models.ForeignKey(
        Device, on_delete=models.PROTECT, related_name="measurements"
    )
    temperature = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal("-80.00")),
            MaxValueValidator(Decimal("150.00")),
        ],
    )
    measured_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=Q(temperature__gte=Decimal("-80.00"))
                & Q(temperature__lte=Decimal("150.00")),
                name="measurement_temp_range",
            )
        ]

    def __str__(self):
        return f"{self.device.serial}: {self.temperature} °C ({self.measured_at})"
