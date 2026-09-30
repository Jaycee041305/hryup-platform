from django.urls import path
from . import views

app_name = 'onboarding'

urlpatterns = [
    path('tracker/', views.TrackerListView.as_view(), name='tracker_list'),
    path('policies/', views.PolicyListView.as_view(), name='policy_list'),
    path('policies/<int:pk>/acknowledge/', views.PolicyAcknowledgeView.as_view(), name='policy_acknowledge'),
]
