from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls', namespace='core')),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('companies/', include('companies.urls', namespace='companies')),
    path('employees/', include('employees.urls', namespace='employees')),
    path('documents/', include('documents.urls', namespace='documents')),
    path('attendance/', include('attendance.urls', namespace='attendance')),
    path('leave/', include('leave.urls', namespace='leave')),
    path('recruitment/', include('recruitment.urls', namespace='recruitment')),
    path('onboarding/', include('onboarding.urls', namespace='onboarding')),
    path('payroll/', include('payroll.urls', namespace='payroll')),
    path('helpdesk/', include('helpdesk.urls', namespace='helpdesk')),
    path('templates-lib/', include('templates_lib.urls', namespace='templates_lib')),
    path('audit/', include('audit.urls', namespace='audit')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
