from django.contrib import admin
from .models import Company, SubscriptionPackage, Subscription

@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'trade_name', 'tin', 'is_active')
    search_fields = ('name', 'trade_name', 'tin', 'registration_number')
    list_filter = ('is_active', 'company_size', 'industry')

@admin.register(SubscriptionPackage)
class SubscriptionPackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'tier', 'price_monthly', 'max_employees', 'is_active')
    list_filter = ('tier', 'is_active')
    search_fields = ('name', 'description')

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('company', 'package', 'status', 'start_date', 'expiry_date', 'billing_cycle')
    list_filter = ('status', 'billing_cycle')
    search_fields = ('company__name', 'package__name')
