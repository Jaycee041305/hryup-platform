from django.contrib import admin
from .models import PayrollPeriod, PayrollEntry

@admin.register(PayrollPeriod)
class PayrollPeriodAdmin(admin.ModelAdmin):
    list_display = ('company', 'start_date', 'end_date', 'status')
    list_filter = ('status', 'company')
    search_fields = ('company__name',)

@admin.register(PayrollEntry)
class PayrollEntryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'period', 'total_hours', 'late_hours', 'absent_days', 'net_compiled_pay')
    list_filter = ('period', 'period__company')
    search_fields = ('employee__user__first_name', 'employee__user__last_name')
