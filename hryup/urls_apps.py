from django.urls import path, include

urlpatterns = [
    path('recruitment/', include('recruitment.urls')),
    path('onboarding/', include('onboarding.urls')),
    path('helpdesk/', include('helpdesk.urls')),
    path('templates/', include('templates_lib.urls')),
]
