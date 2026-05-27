from django.contrib import admin
from .models import Tenant, DataSource, ActivityRow, AuditLog

@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'created_at']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(DataSource)
class DataSourceAdmin(admin.ModelAdmin):
    list_display = ['tenant', 'source_type', 'status', 'row_count', 'error_count', 'ingested_at']
    list_filter = ['source_type', 'status']

@admin.register(ActivityRow)
class ActivityRowAdmin(admin.ModelAdmin):
    list_display = ['category', 'scope', 'activity_date', 'status', 'tenant', 'locked']
    list_filter = ['scope', 'category', 'status']
    search_fields = ['vendor', 'location', 'raw_reference']

@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['activity_row', 'action', 'changed_by', 'changed_at']
    list_filter = ['action']