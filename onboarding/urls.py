from django.urls import path
from . import views

app_name = 'onboarding'

urlpatterns = [
    path('tracker/', views.TrackerListView.as_view(), name='tracker_list'),
    path('tracker/assign/', views.AssignOnboardingView.as_view(), name='tracker_assign'),
    path('tracker/<int:pk>/', views.TrackerDetailView.as_view(), name='tracker_detail'),
    path('tracker/<int:pk>/task/<int:task_id>/toggle/', views.ToggleTaskView.as_view(), name='toggle_task'),
    path('policies/', views.PolicyListView.as_view(), name='policy_list'),
    path('policies/<int:pk>/acknowledge/', views.PolicyAcknowledgeView.as_view(), name='policy_acknowledge'),
]
