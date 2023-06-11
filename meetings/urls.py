from django.urls import path
from . import views
from meetings.views import MeetingPDFView
from django.contrib.auth.views import LogoutView

app_name = 'meetings'

urlpatterns = [
    path('', views.homepage, name='homepage'),
    path('meeting-form/', views.meeting_form, name='meeting_form'),
    path('meeting-detail/<int:meeting_id>/', views.meeting_detail, name='meeting_detail'),
    path('meeting-pdf/<int:meeting_id>/', MeetingPDFView.as_view(), name='meeting_pdf'),
    path('meeting-delete/<int:meeting_id>/', views.meeting_delete, name='meeting_delete'),
    path('meeting-edit/<int:meeting_id>/', views.meeting_edit, name='meeting_edit'),    
    path('members-form/', views.members_form, name='members_form'),
    path('member-delete/<int:member_id>/', views.member_delete, name='member_delete'),
    path('member-info/<int:member_id>/', views.member_info, name='member_info'),
    path('months/', views.months_view, name='months'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
]
