from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from accounts.models import StudentProfile, WardenProfile, CustomUser
from accounts.forms import CustomUserCreationForm, StudentProfileForm, StudentProfileUpdateForm, CustomUserUpdateForm, WardenProfileForm
from core.models import RoomAllocation, Room
from operations.models import Complaint, Fee, Attendance, Visitor, LeaveApplication, MaintenanceRequest, Announcement, Event, RoomRating, Notification
from operations.forms import ComplaintForm, ComplaintResolutionForm, VisitorForm, LeaveApplicationForm, MaintenanceRequestForm, RoomRatingForm
from datetime import datetime, timedelta


# ==================== NOTIFICATION HELPER FUNCTIONS ====================

def create_notification(recipient, title, message, notification_type='info', sender=None, related_model=None, related_id=None):
    """Helper function to create notifications"""
    try:
        notification = Notification.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            sender=sender,
            related_model=related_model,
            related_id=related_id,
        )
        return notification
    except Exception as e:
        print(f"Error creating notification: {e}")
        return None


def is_student(user):
    return user.role == 'student'


def is_warden(user):
    return user.role == 'warden'


def is_admin(user):
    return user.role == 'admin'


# ==================== AUTHENTICATION VIEWS ====================

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        
        if not username or not password:
            messages.error(request, 'Please enter both username and password')
            return render(request, 'login.html')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            if not user.is_active:
                messages.error(request, 'Your account has been deactivated. Contact admin.')
                return render(request, 'login.html')
            
            login(request, user)
            user.last_login_ip = request.META.get('REMOTE_ADDR', '')
            user.save()
            
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            
            # Create notification about attendance for students
            if user.role == 'student':
                try:
                    student = user.student_profile
                    today = datetime.now().date()
                    
                    # Check today's attendance
                    today_attendance = Attendance.objects.filter(
                        student=student,
                        date=today
                    ).first()
                    
                    if today_attendance:
                        status_display = today_attendance.get_status_display()
                        message = f"Your attendance for {today.strftime('%d %B %Y')} is marked as: {status_display}"
                        create_notification(
                            recipient=user,
                            title="Today's Attendance",
                            message=message,
                            notification_type='info',
                            related_model='attendance',
                            related_id=today_attendance.id
                        )
                    else:
                        message = f"No attendance record found for {today.strftime('%d %B %Y')}"
                        create_notification(
                            recipient=user,
                            title="Attendance Status",
                            message=message,
                            notification_type='warning'
                        )
                    
                    # Check for pending fees
                    pending_fees = Fee.objects.filter(student=student, status='pending')
                    if pending_fees.exists():
                        total_pending = pending_fees.aggregate(Sum('amount'))['amount__sum'] or 0
                        create_notification(
                            recipient=user,
                            title="Pending Fees Alert",
                            message=f"You have ₹{total_pending} in pending fees. Please pay to avoid penalties.",
                            notification_type='warning'
                        )
                    
                    # Check for pending complaints
                    pending_complaints = Complaint.objects.filter(student=student, status='pending')
                    if pending_complaints.exists():
                        count = pending_complaints.count()
                        create_notification(
                            recipient=user,
                            title="Pending Complaints",
                            message=f"You have {count} pending complaint(s) that need your attention.",
                            notification_type='info'
                        )
                
                except StudentProfile.DoesNotExist:
                    pass
            
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('login')


def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            messages.success(request, 'Registration successful! Your account is pending admin approval. You will receive an email once approved.')
            return redirect('login')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = CustomUserCreationForm()

    return render(request, 'register.html', {'form': form})


# ==================== DASHBOARD VIEWS ====================

@login_required
def dashboard_redirect(request):
    """Redirect to appropriate dashboard based on user role"""
    if request.user.role == 'student':
        return redirect('student_dashboard')
    elif request.user.role == 'warden':
        return redirect('warden_dashboard')
    else:
        return redirect('/admin/')


@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Student profile not found. Please complete your profile.')
        return redirect('profile')
    
    room = RoomAllocation.objects.filter(student=student, is_active=True).first()
    complaints = Complaint.objects.filter(student=student).order_by('-created_at')
    pending_complaints = complaints.filter(status='pending').count()
    complaints = complaints[:5]
    
    fees = Fee.objects.filter(student=student)
    pending_fees = fees.filter(status='pending').aggregate(Sum('amount'))['amount__sum'] or 0
    
    attendance_today = Attendance.objects.filter(
        student=student,
        date=datetime.now().date()
    ).first()
    
    # Get recent attendance logs (last 7 days)
    attendance_logs = Attendance.objects.filter(student=student).order_by('-date')[:7]
    
    recent_announcements = Announcement.objects.filter(is_active=True).order_by('-created_at')[:5]
    upcoming_events = Event.objects.filter(
        event_date__gte=datetime.now().date()
    ).order_by('event_date')[:5]
    
    leave_applications = LeaveApplication.objects.filter(student=student).order_by('-created_at')
    pending_leave = leave_applications.filter(status='pending').count()
    leave_applications = leave_applications[:3]
    
    visitors_today = Visitor.objects.filter(
        student=student,
        visit_date=datetime.now().date()
    )
    
    context = {
        'student': student,
        'room': room,
        'complaints': list(complaints),
        'pending_complaints': pending_complaints,
        'fees': fees,
        'pending_fees': pending_fees,
        'total_fees': fees.aggregate(Sum('amount'))['amount__sum'] or 0,
        'attendance_today': attendance_today,
        'attendance_logs': attendance_logs,
        'recent_announcements': recent_announcements,
        'upcoming_events': upcoming_events,
        'leave_applications': leave_applications,
        'pending_leave': pending_leave,
        'visitors_today': visitors_today,
    }
    
    return render(request, 'student_dashboard.html', context)


@login_required
@user_passes_test(is_warden)
def warden_dashboard(request):
    # Get pending registrations
    pending_registrations = CustomUser.objects.filter(is_active=False, role='student').order_by('-created_at')

    # Get pending complaints
    complaints = Complaint.objects.filter(status='pending').order_by('-created_at')

    # Get total students
    total_students = CustomUser.objects.filter(is_active=True, role='student').count()

    # Get total fees
    total_fees = Fee.objects.count()

    context = {
        'pending_registrations': pending_registrations,
        'complaints': complaints,
        'total_students': total_students,
        'total_fees': total_fees,
    }

    return render(request, 'warden_dashboard.html', context)


# ==================== PROFILE VIEWS ====================

@login_required
def profile_view(request):
    user = request.user
    context = {'user': user}
    
    if user.role == 'student':
        try:
            context['student_profile'] = user.student_profile
            context['room_allocation'] = RoomAllocation.objects.filter(
                student=user.student_profile,
                is_active=True
            ).first()
        except StudentProfile.DoesNotExist:
            pass
    elif user.role == 'warden':
        try:
            context['warden_profile'] = user.warden_profile
        except WardenProfile.DoesNotExist:
            pass
    
    return render(request, 'profile.html', context)


@login_required
def edit_profile(request):
    user = request.user
    
    if request.method == 'POST':
        user_form = CustomUserUpdateForm(request.POST, request.FILES, instance=user)
        
        if user.role == 'student':
            student_form = StudentProfileUpdateForm(request.POST, request.FILES, instance=user.student_profile)
            if user_form.is_valid() and student_form.is_valid():
                user_form.save()
                student_form.save()
                messages.success(request, 'Profile updated successfully')
                return redirect('profile')
        elif user.role == 'warden':
            warden_form = WardenProfileForm(request.POST, instance=user.warden_profile)
            if user_form.is_valid() and warden_form.is_valid():
                user_form.save()
                warden_form.save()
                messages.success(request, 'Profile updated successfully')
                return redirect('profile')
        else:
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'Profile updated successfully')
                return redirect('profile')
    else:
        user_form = CustomUserUpdateForm(instance=user)
        context = {'user_form': user_form}
        
        if user.role == 'student':
            student_form = StudentProfileUpdateForm(instance=user.student_profile)
            context['student_form'] = student_form
        elif user.role == 'warden':
            warden_form = WardenProfileForm(instance=user.warden_profile)
            context['warden_form'] = warden_form
        
        return render(request, 'edit_profile.html', context)
    
    messages.error(request, 'Error updating profile')
    return render(request, 'edit_profile.html', context)


# ==================== COMPLAINT VIEWS ====================

@login_required
@user_passes_test(is_student)
def student_complaints(request):
    student = request.user.student_profile
    complaints = Complaint.objects.filter(student=student).order_by('-created_at')
    
    status_filter = request.GET.get('status')
    if status_filter:
        complaints = complaints.filter(status=status_filter)
    
    category_filter = request.GET.get('category')
    if category_filter:
        complaints = complaints.filter(category=category_filter)
    
    context = {
        'complaints': complaints,
        'status_choices': Complaint.STATUS_CHOICES,
        'category_choices': Complaint.CATEGORY_CHOICES,
        'selected_status': status_filter,
        'selected_category': category_filter,
    }
    
    return render(request, 'complaints/student_complaints.html', context)


@login_required
@user_passes_test(is_student)
def add_complaint(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.student = request.user.student_profile
            complaint.save()
            
            # Create notification for the student
            create_notification(
                recipient=request.user,
                title='Complaint Submitted',
                message=f"Your complaint '{complaint.title}' has been successfully submitted and is awaiting review.",
                notification_type='success',
                related_model='complaint',
                related_id=complaint.id
            )
            
            messages.success(request, 'Complaint submitted successfully')
            return redirect('student_complaints')
    else:
        form = ComplaintForm()
    
    return render(request, 'complaints/add_complaint.html', {'form': form})


@login_required
def complaint_detail(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    
    if request.user.role == 'student' and complaint.student.user != request.user:
        return HttpResponseForbidden('You do not have permission to view this complaint')
    elif request.user.role == 'warden':
        pass
    
    return render(request, 'complaints/complaint_detail.html', {'complaint': complaint})


@login_required
@user_passes_test(is_student)
def edit_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id, student=request.user.student_profile)

    if not complaint.is_editable:
        messages.error(request, 'You can only edit a complaint while it is still open.')
        return redirect('complaint_detail', complaint_id=complaint.id)

    if request.method == 'POST':
        form = ComplaintForm(request.POST, request.FILES, instance=complaint)
        if form.is_valid():
            form.save()
            messages.success(request, 'Complaint updated successfully.')
            return redirect('complaint_detail', complaint_id=complaint.id)
    else:
        form = ComplaintForm(instance=complaint)

    return render(request, 'complaints/edit_complaint.html', {'form': form, 'complaint': complaint})


@login_required
@user_passes_test(is_student)
def apply_leave(request):
    if request.method == 'POST':
        form = LeaveApplicationForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.student = request.user.student_profile
            leave.status = 'pending'
            leave.save()
            
            # Create notification
            create_notification(
                recipient=request.user,
                title='Leave Request Submitted',
                message=f"Your leave request from {leave.leave_from} to {leave.leave_to} has been submitted and is pending warden approval.",
                notification_type='info',
                related_model='leave',
                related_id=leave.id
            )
            
            messages.success(request, 'Leave request submitted and sent for warden approval.')
            return redirect('student_leave_requests')
    else:
        form = LeaveApplicationForm()

    return render(request, 'leave/apply_leave.html', {'form': form})


@login_required
@user_passes_test(is_student)
def student_leave_requests(request):
    leave_applications = LeaveApplication.objects.filter(student=request.user.student_profile).order_by('-created_at')
    context = {
        'leave_applications': leave_applications,
    }
    return render(request, 'leave/student_leave_requests.html', context)


@login_required
@user_passes_test(is_warden)
def warden_leave_requests(request):
    leave_requests = LeaveApplication.objects.filter(status='pending').order_by('-created_at')

    if request.method == 'POST':
        leave_id = request.POST.get('leave_id')
        action = request.POST.get('action')
        notes = request.POST.get('notes', '').strip()

        try:
            leave = LeaveApplication.objects.get(id=leave_id, status='pending')
            leave.approved_by = request.user.warden_profile
            leave.approval_notes = notes
            if action == 'approve':
                leave.status = 'approved'
                create_notification(
                    recipient=leave.student.user,
                    title='Leave Approved',
                    message=f'Your leave request from {leave.leave_from} to {leave.leave_to} has been approved.',
                    notification_type='success',
                    sender=request.user,
                    related_model='leave',
                    related_id=leave.id
                )
                messages.success(request, 'Leave request approved.')
            else:
                leave.status = 'rejected'
                create_notification(
                    recipient=leave.student.user,
                    title='Leave Rejected',
                    message=f'Your leave request from {leave.leave_from} to {leave.leave_to} has been rejected.',
                    notification_type='error',
                    sender=request.user,
                    related_model='leave',
                    related_id=leave.id
                )
                messages.success(request, 'Leave request rejected.')
            leave.save()
        except LeaveApplication.DoesNotExist:
            messages.error(request, 'Leave request not found or already processed.')

        return redirect('warden_leave_requests')

    return render(request, 'warden/leave_requests.html', {'leave_requests': leave_requests})


@login_required
@user_passes_test(is_warden)
def review_leave_application(request, leave_id):
    leave = get_object_or_404(LeaveApplication, id=leave_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '').strip()

        if action == 'approve':
            leave.status = 'approved'
            leave.approved_by = request.user.warden_profile
            leave.approval_notes = notes
            leave.save()
            create_notification(
                recipient=leave.student.user,
                title='Leave Approved',
                message=f'Your leave request from {leave.leave_from} to {leave.leave_to} has been approved.',
                notification_type='success',
                sender=request.user,
                related_model='leave',
                related_id=leave.id
            )
            messages.success(request, 'Leave request approved.')
        elif action == 'reject':
            leave.status = 'rejected'
            leave.approved_by = request.user.warden_profile
            leave.approval_notes = notes
            leave.save()
            create_notification(
                recipient=leave.student.user,
                title='Leave Rejected',
                message=f'Your leave request from {leave.leave_from} to {leave.leave_to} has been rejected.',
                notification_type='error',
                sender=request.user,
                related_model='leave',
                related_id=leave.id
            )
            messages.success(request, 'Leave request rejected.')
        else:
            messages.error(request, 'Invalid action.')

        return redirect('warden_leave_requests')

    return render(request, 'warden/review_leave.html', {'leave': leave})


@login_required
@user_passes_test(is_warden)
def warden_complaints(request):
    complaints = Complaint.objects.filter(status='pending').order_by('-priority', '-created_at')
    
    context = {
        'complaints': complaints,
        'status_choices': Complaint.STATUS_CHOICES,
    }
    
    return render(request, 'warden/complaints.html', context)


@login_required
@user_passes_test(is_warden)
def resolve_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)

    if request.method == 'POST':
        form = ComplaintResolutionForm(request.POST, instance=complaint)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.resolved_by = request.user.warden_profile
            complaint.resolved_at = timezone.now()
            complaint.save()

            # Create notification for the student
            create_notification(
                recipient=complaint.student.user,
                title=f"Complaint Resolved: {complaint.title}",
                message=f"Your complaint '{complaint.title}' status updated to {complaint.get_status_display()}. {complaint.resolution_notes or ''}",
                notification_type='success' if complaint.status == 'resolved' else 'warning',
                sender=request.user,
                related_model='complaint',
                related_id=complaint.id
            )

            messages.success(request, 'Complaint resolved successfully')
            return redirect('warden_complaints')
    else:
        form = ComplaintResolutionForm(instance=complaint)

    return render(request, 'warden/resolve_complaint.html', {'form': form, 'complaint': complaint})


# ==================== FEE VIEWS ====================

@login_required
@user_passes_test(is_student)
def student_fees(request):
    student = request.user.student_profile
    fees = Fee.objects.filter(student=student).order_by('-due_date')
    
    context = {
        'fees': fees,
        'total_amount': fees.aggregate(Sum('amount'))['amount__sum'] or 0,
        'paid_amount': fees.filter(status='paid').aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0,
        'pending_amount': fees.filter(status__in=['pending', 'overdue']).aggregate(Sum('amount'))['amount__sum'] or 0,
    }
    
    return render(request, 'fees/student_fees.html', context)


@login_required
def fee_detail(request, fee_id):
    fee = get_object_or_404(Fee, id=fee_id)
    
    if request.user.role == 'student' and fee.student.user != request.user:
        return HttpResponseForbidden('You do not have permission to view this fee')
    
    return render(request, 'fees/fee_detail.html', {'fee': fee})


# ==================== NOTIFICATION VIEWS ====================

@login_required
def notifications_view(request):
    """View for displaying user notifications"""
    notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')

    # Mark notifications as read when viewed (optional - could be done via AJAX)
    if request.method == 'POST' and 'mark_read' in request.POST:
        notification_id = request.POST.get('notification_id')
        if notification_id:
            try:
                notification = Notification.objects.get(id=notification_id, recipient=request.user)
                notification.mark_as_read()
                messages.success(request, 'Notification marked as read')
            except Notification.DoesNotExist:
                messages.error(request, 'Notification not found')
        return redirect('notifications')

    # Get unread count
    unread_count = notifications.filter(is_read=False).count()

    context = {
        'notifications': notifications,
        'unread_count': unread_count,
    }

    return render(request, 'notifications.html', context)


@login_required
def mark_notification_read(request, notification_id):
    """AJAX endpoint to mark notification as read"""
    if request.method == 'POST':
        try:
            notification = Notification.objects.get(id=notification_id, recipient=request.user)
            notification.mark_as_read()
            return JsonResponse({'success': True})
        except Notification.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Notification not found'})
    return JsonResponse({'success': False, 'error': 'Invalid request'})


# ==================== ADMIN VIEWS ====================

@login_required
@user_passes_test(lambda u: u.is_staff or u.role == 'admin' or u.role == 'warden')
def pending_registrations(request):
    """Admin/Warden view to approve pending student registrations"""
    pending_users = CustomUser.objects.filter(is_active=False, role='student').order_by('-created_at')

    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')

        if user_id and action in ['approve', 'reject']:
            try:
                user = CustomUser.objects.get(id=user_id, is_active=False, role='student')

                if action == 'approve':
                    user.is_active = True
                    user.save()

                    # Create notification for approved user
                    create_notification(
                        recipient=user,
                        title="Account Approved",
                        message="Your account has been approved! You can now login to the system.",
                        notification_type='success',
                        sender=request.user
                    )

                    messages.success(request, f'Account for {user.username} has been approved.')
                else:
                    # Delete rejected user
                    user.delete()
                    messages.success(request, f'Account for {user.username} has been rejected.')

            except CustomUser.DoesNotExist:
                messages.error(request, 'User not found.')

        return redirect('pending_registrations')

    context = {
        'pending_users': pending_users,
        'pending_count': pending_users.count(),
    }

    return render(request, 'admin/pending_registrations.html', context)