from django.db import models
from django.contrib.auth.models import User


class Tenant(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class DataSource(models.Model):
    SOURCE_TYPES = [
        ('SAP', 'SAP Fuel & Procurement'),
        ('UTILITY', 'Utility Electricity'),
        ('TRAVEL', 'Corporate Travel'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('DONE', 'Done'),
        ('FAILED', 'Failed'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name='sources')
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES)
    ingest_mode = models.CharField(max_length=50, default='FILE_UPLOAD')
    raw_file = models.FileField(upload_to='uploads/', null=True, blank=True)
    ingested_at = models.DateTimeField(auto_now_add=True)
    ingested_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    row_count = models.IntegerField(default=0)
    error_count = models.IntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')

    def __str__(self):
        return f"{self.tenant.name} - {self.source_type} - {self.ingested_at}"


class ActivityRow(models.Model):
    SCOPE_CHOICES = [(1, 'Scope 1'), (2, 'Scope 2'), (3, 'Scope 3')]
    CATEGORY_CHOICES = [
        ('FUEL', 'Fuel'),
        ('ELECTRICITY', 'Electricity'),
        ('FLIGHT', 'Flight'),
        ('HOTEL', 'Hotel'),
        ('GROUND_TRANSPORT', 'Ground Transport'),
        ('PROCUREMENT', 'Procurement'),
    ]
    STATUS_CHOICES = [
        ('PENDING', 'Pending Review'),
        ('FLAGGED', 'Flagged'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    data_source = models.ForeignKey(DataSource, on_delete=models.CASCADE, related_name='rows')
    scope = models.IntegerField(choices=SCOPE_CHOICES)
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)

    # Raw values from source
    raw_quantity = models.CharField(max_length=100, blank=True)
    raw_unit = models.CharField(max_length=50, blank=True)
    raw_currency = models.CharField(max_length=10, blank=True)
    raw_date_str = models.CharField(max_length=50, blank=True)
    raw_reference = models.CharField(max_length=255, blank=True)
    raw_payload = models.JSONField(default=dict)

    # Normalized values
    quantity_kwh = models.FloatField(null=True, blank=True)
    quantity_liters = models.FloatField(null=True, blank=True)
    quantity_km = models.FloatField(null=True, blank=True)
    activity_date = models.DateField(null=True, blank=True)

    # Metadata
    location = models.CharField(max_length=255, blank=True)
    vendor = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    # Review state
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    flag_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    locked = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.category} - {self.activity_date} - {self.status}"


class AuditLog(models.Model):
    activity_row = models.ForeignKey(ActivityRow, on_delete=models.CASCADE, related_name='audit_logs')
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    field_changed = models.CharField(max_length=100)
    old_value = models.TextField(blank=True)
    new_value = models.TextField(blank=True)
    action = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.action} by {self.changed_by} at {self.changed_at}"