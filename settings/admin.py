from django.contrib import admin
from .models import (
    SettingCategory,
    SettingDefinition,
    Setting,
    CredentialStore,
    EmailConfiguration,
    SocialMediaCredential
)

@admin.register(SettingCategory)
class SettingCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'parent', 'order', 'is_active')
    list_filter = ('is_active', 'parent')
    search_fields = ('name', 'key', 'description')
    ordering = ('order', 'name')

@admin.register(SettingDefinition)
class SettingDefinitionAdmin(admin.ModelAdmin):
    list_display = ('name', 'key', 'category', 'setting_type', 'is_required', 'is_sensitive', 'is_active')
    list_filter = ('category', 'setting_type', 'is_required', 'is_sensitive', 'is_active')
    search_fields = ('name', 'key', 'description')
    ordering = ('category', 'order', 'name')

@admin.register(Setting)
class SettingAdmin(admin.ModelAdmin):
    list_display = ('definition', 'get_masked_value', 'is_active', 'updated_at')
    list_filter = ('is_active', 'definition__category')
    search_fields = ('definition__name', 'definition__key')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

@admin.register(CredentialStore)
class CredentialStoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'service', 'credential_type', 'environment', 'is_active', 'expires_at')
    list_filter = ('credential_type', 'environment', 'is_active')
    search_fields = ('name', 'service', 'key')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

@admin.register(EmailConfiguration)
class EmailConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'provider', 'from_email', 'is_active', 'is_default')
    list_filter = ('provider', 'is_active', 'is_default')
    search_fields = ('name', 'from_email', 'from_name')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')

@admin.register(SocialMediaCredential)
class SocialMediaCredentialAdmin(admin.ModelAdmin):
    list_display = ('platform', 'environment', 'is_active', 'updated_at')
    list_filter = ('platform', 'environment', 'is_active')
    search_fields = ('platform', 'business_account_id')
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by')
