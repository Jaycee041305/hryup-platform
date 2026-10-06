from django.contrib import admin
from .models import OnboardingTemplate, OnboardingTask, EmployeeOnboarding, EmployeeOnboardingTask, PolicyDocument, PolicyAcknowledgment

class OnboardingTaskInline(admin.TabularInline):
    model = OnboardingTask
    extra = 1

@admin.register(OnboardingTemplate)
class OnboardingTemplateAdmin(admin.ModelAdmin):
    list_display = ('title', 'company')
    list_filter = ('company',)
    inlines = [OnboardingTaskInline]

@admin.register(EmployeeOnboarding)
class EmployeeOnboardingAdmin(admin.ModelAdmin):
    list_display = ('employee', 'template', 'status', 'company')
    list_filter = ('status', 'company')

admin.site.register(EmployeeOnboardingTask)
admin.site.register(PolicyDocument)
admin.site.register(PolicyAcknowledgment)
