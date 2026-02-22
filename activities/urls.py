from django.urls import path
from . import views

urlpatterns = [
    path('activities/', views.activity_list, name='activity-list'),
    path('activities/create/', views.create_activity, name='create-activity'),
    path('activities/<int:activity_id>/', views.activity_detail, name='activity-detail'),
    path('activities/<int:activity_id>/register/', views.register_activity, name='register-activity'),
    path('activities/<int:activity_id>/cancel-registration/', views.cancel_registration, name='cancel-registration'),
    path('activities/<int:activity_id>/cancel/', views.cancel_activity, name='cancel-activity'),
    path('activities/<int:activity_id>/participants/', views.participants, name='participants'),
    path('activities/<int:activity_id>/comments/', views.comments, name='comments'),
    path('student/schedule/', views.student_schedule, name='student-schedule'),
]
