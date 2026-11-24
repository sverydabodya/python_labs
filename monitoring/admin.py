from django.contrib import admin

from .models import Device, Measurement, Passport, Tag


@admin.register(Device)
class DeviceAdmin(admin.ModelAdmin):
    list_display = ["name", "serial"]
    search_fields = ["name", "serial"]


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name"]
    search_fields = ["name"]


@admin.register(Passport)
class PassportAdmin(admin.ModelAdmin):
    list_display = ["device", "location"]
    search_fields = ["device__serial", "location"]


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ["device", "temperature", "measured_at"]
    list_filter = ["device"]
