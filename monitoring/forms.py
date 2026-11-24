from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import Device, Measurement


class MeasurementForm(forms.ModelForm):
    class Meta:
        model = Measurement
        fields = ["device", "temperature", "measured_at"]

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["device"].queryset = Device.objects.filter(owner=user).order_by(
            "serial"
        )

    def clean_measured_at(self):
        measured_at = self.cleaned_data.get("measured_at")
        if measured_at and measured_at > timezone.now():
            raise ValidationError("Час вимірювання не може бути в майбутньому.")
        return measured_at
