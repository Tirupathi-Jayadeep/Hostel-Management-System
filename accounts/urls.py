from django.urls import path
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    
    # Dashboards
    path('', views.dashboard_redirect, name='dashboard'),
    path('student/', login_required(views.student_dashboard), name='student_dashboard'),
    path('warden/', login_required(views.warden_dashboard), name='warden_dashboard'),
    
    # Profile
    path('profile/', login_required(views.profile_view), name='profile'),
    path('profile/edit/', login_required(views.edit_profile), name='edit_profile'),
    
    # Complaints
    path('complaints/', login_required(views.student_complaints), name='student_complaints'),
    path('add-complaint/', login_required(views.add_complaint), name='add_complaint'),
    path('complaint/<int:complaint_id>/edit/', login_required(views.edit_complaint), name='edit_complaint'),
    path('complaint/<int:complaint_id>/', login_required(views.complaint_detail), name='complaint_detail'),
    
    # Leave management
    path('leave/apply/', login_required(views.apply_leave), name='apply_leave'),
    path('leave/requests/', login_required(views.student_leave_requests), name='student_leave_requests'),
    path('warden/leave-requests/', login_required(views.warden_leave_requests), name='warden_leave_requests'),
    path('leave/<int:leave_id>/review/', login_required(views.review_leave_application), name='review_leave_application'),
    
    # Warden - Complaint Management
    path('warden/complaints/', login_required(views.warden_complaints), name='warden_complaints'),
    path('complaint/<int:complaint_id>/resolve/', login_required(views.resolve_complaint), name='resolve_complaint'),
    
    # Fee Management
    path('fees/', login_required(views.student_fees), name='student_fees'),
    path('fee/<int:fee_id>/', login_required(views.fee_detail), name='fee_detail'),
    
    # Notifications
    path('notifications/', login_required(views.notifications_view), name='notifications'),
    path('notification/<int:notification_id>/read/', login_required(views.mark_notification_read), name='mark_notification_read'),
    
    # Password Reset
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='password_reset_complete.html'), name='password_reset_complete'),
    
    # Admin Views
    path('admin/pending-registrations/', views.pending_registrations, name='pending_registrations'),
]