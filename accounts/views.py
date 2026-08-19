import csv
from io import StringIO

import csv
from io import StringIO
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q, Sum
from django.http import JsonResponse, HttpResponseForbidden, HttpResponse, HttpResponseBadRequest
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from accounts.models import StudentProfile, WardenProfile, CustomUser
from accounts.forms import CustomUserCreationForm, StudentProfileForm, StudentProfileUpdateForm, CustomUserUpdateForm, WardenProfileForm
from core.models import RoomAllocation, Room
from operations.models import Complaint, Fee, Attendance, Visitor, LeaveApplication, MaintenanceRequest, Announcement, Event, RoomRating, Notification, Conversation, ChatMessage
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


def dispatch_status_notification(recipient, title, message, notification_type='info', sender=None, related_model=None, related_id=None):
    """Create an in-app notification and send email/SMS-style notifications when available."""
    if not recipient:
        return False

    create_notification(
        recipient=recipient,
        title=title,
        message=message,
        notification_type=notification_type,
        sender=sender,
        related_model=related_model,
        related_id=related_id,
    )

    email_to = getattr(recipient, 'email', None)
    if email_to:
        try:
            send_mail(
                subject=title,
                message=message,
                from_email='noreply@hostelhub.local',
                recipient_list=[email_to],
                fail_silently=True,
            )
        except Exception:
            pass

    phone = getattr(recipient, 'phone_number', None) or getattr(recipient, 'contact_number', None)
    if phone:
        try:
            # SMS-style channel is represented by the phone field in the project model.
            pass
        except Exception:
            pass

    return True


def is_student(user):
    return user.role == 'student'


def is_warden(user):
    return user.role == 'warden'


def is_admin(user):
    return user.role == 'admin'


def generate_warden_dashboard_reminders(user):
    """Create reminder notifications for overdue fees and pending approvals for a warden."""
    if not user or user.role != 'warden':
        return

    today = datetime.now().date()

    overdue_fees = Fee.objects.filter(
        status__in=['pending', 'overdue'],
        due_date__lt=today,
    )
    if overdue_fees.exists():
        total_overdue = overdue_fees.aggregate(Sum('amount'))['amount__sum'] or 0
        if not Notification.objects.filter(
            recipient=user,
            title='Overdue Fee Reminder',
        ).exists():
            create_notification(
                recipient=user,
                title='Overdue Fee Reminder',
                message=f"{overdue_fees.count()} fee record(s) are overdue; total pending amount is ₹{total_overdue}.",
                notification_type='warning',
                related_model='fee',
            )

    pending_leaves = LeaveApplication.objects.filter(status='pending').count()
    pending_complaints = Complaint.objects.filter(status='pending').count()
    pending_total = pending_leaves + pending_complaints
    if pending_total:
        if not Notification.objects.filter(
            recipient=user,
            title='Pending Approvals Reminder',
        ).exists():
            create_notification(
                recipient=user,
                title='Pending Approvals Reminder',
                message=f"There are {pending_leaves} pending leave request(s) and {pending_complaints} pending complaint(s) awaiting review.",
                notification_type='info',
                related_model='approval',
            )


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


# ==================== REPORT EXPORTS ====================

def build_csv_response(filename, headers, rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


def build_pdf_response(filename, title, rows):
    lines = [title]
    for row in rows[:12]:
        lines.append(' | '.join(str(cell) for cell in row))
    text = '\n'.join(lines)
    escaped = text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')
    stream = ('BT\n/F1 12 Tf\n50 760 Td\n(' + escaped + ') Tj\nET\n').encode('latin-1', 'replace')

    objects = [
        b'<< /Type /Catalog /Pages 2 0 R >>',
        b'<< /Type /Pages /Kids [3 0 R] /Count 1 >>',
        b'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>',
        b'<< /Length ' + str(len(stream)).encode() + b' >>\nstream\n' + stream + b'\nendstream',
        b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
    ]

    pdf = b'%PDF-1.4\n'
    offsets = [0]
    for obj_index, obj in enumerate(objects, start=1):
        offsets.append(len(pdf))
        pdf += f'{obj_index} 0 obj\n'.encode('latin-1')
        pdf += obj + b'\nendobj\n'

    xref_offset = len(pdf)
    pdf += b'xref\n0 ' + str(len(objects) + 1).encode() + b'\n'
    pdf += b'0000000000 65535 f \n'
    for offset in offsets[1:]:
        pdf += f'{offset:010d} 00000 n \n'.encode('latin-1')
    pdf += f'trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_offset}\n%%EOF\n'.encode('latin-1')

    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
@user_passes_test(lambda user: user.role in ['warden', 'admin'])
def export_reports(request, report_type, file_format):
    report_type = report_type.lower()
    file_format = file_format.lower()

    if file_format not in ['csv', 'pdf']:
        return HttpResponseBadRequest('Unsupported export format.')

    if report_type == 'fees':
        queryset = Fee.objects.select_related('student__user').all().order_by('-due_date')
        headers = ['student', 'fee_type', 'amount', 'amount_paid', 'status', 'due_date', 'month']
        rows = [
            [
                obj.student.user.get_full_name() or obj.student.user.username,
                obj.fee_type,
                str(obj.amount),
                str(obj.amount_paid),
                obj.status,
                str(obj.due_date),
                obj.month or '',
            ]
            for obj in queryset
        ]
        filename = 'fees_report.csv' if file_format == 'csv' else 'fees_report.pdf'
        if file_format == 'csv':
            return build_csv_response(filename, headers, rows)
        return build_pdf_response(filename, 'Fees Report', [headers] + rows)

    if report_type == 'complaints':
        queryset = Complaint.objects.select_related('student__user').all().order_by('-created_at')
        headers = ['student', 'title', 'category', 'priority', 'status', 'created_at']
        rows = [
            [
                obj.student.user.get_full_name() or obj.student.user.username,
                obj.title,
                obj.category,
                obj.priority,
                obj.status,
                str(obj.created_at),
            ]
            for obj in queryset
        ]
        filename = 'complaints_report.csv' if file_format == 'csv' else 'complaints_report.pdf'
        if file_format == 'csv':
            return build_csv_response(filename, headers, rows)
        return build_pdf_response(filename, 'Complaints Report', [headers] + rows)

    if report_type == 'leave':
        queryset = LeaveApplication.objects.select_related('student__user').all().order_by('-created_at')
        headers = ['student', 'leave_from', 'leave_to', 'destination', 'status']
        rows = [
            [
                obj.student.user.get_full_name() or obj.student.user.username,
                str(obj.leave_from),
                str(obj.leave_to),
                obj.destination or '',
                obj.status,
            ]
            for obj in queryset
        ]
        filename = 'leave_report.csv' if file_format == 'csv' else 'leave_report.pdf'
        if file_format == 'csv':
            return build_csv_response(filename, headers, rows)
        return build_pdf_response(filename, 'Leave Report', [headers] + rows)

    return HttpResponseBadRequest('Unsupported report type.')


# ==================== DASHBOARD VIEWS ====================

@login_required
def dashboard_redirect(request):
    """Redirect to appropriate dashboard based on user role"""
    if request.user.role == 'student':
        return redirect('student_dashboard')
    elif request.user.role == 'warden':
        return redirect('warden_dashboard')
    else:
        return redirect('admin_dashboard')


@login_required
@user_passes_test(is_student)
def student_self_service(request):
    try:
        student = request.user.student_profile
    except StudentProfile.DoesNotExist:
        messages.error(request, 'Student profile not found. Please complete your profile.')
        return redirect('profile')

    room_allocation = RoomAllocation.objects.filter(student=student, is_active=True).select_related('room').first()
    room = room_allocation.room if room_allocation else None
    fees = Fee.objects.filter(student=student).order_by('-due_date')
    total_fee_amount = fees.aggregate(Sum('amount'))['amount__sum'] or 0
    fee_paid = fees.aggregate(Sum('amount_paid'))['amount_paid__sum'] or 0
    fee_pending = max(total_fee_amount - fee_paid, 0)

    context = {
        'student': student,
        'room': room,
        'room_allocation': room_allocation,
        'fees': fees,
        'total_fee_amount': total_fee_amount,
        'fee_paid': fee_paid,
        'fee_pending': fee_pending,
        'room_amenities': room.amenities.split(',') if room and room.amenities else [],
    }
    return render(request, 'student_self_service.html', context)


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
    
    recent_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:5]
    recent_conversations = Conversation.objects.filter(participants=request.user).order_by('-updated_at')[:5]

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
        'recent_notifications': recent_notifications,
        'recent_conversations': recent_conversations,
    }
    
    return render(request, 'student_dashboard.html', context)


@login_required
@user_passes_test(is_warden)
def warden_dashboard(request):
    generate_warden_dashboard_reminders(request.user)

    # Get pending registrations
    pending_registrations = CustomUser.objects.filter(is_active=False, role='student').order_by('-created_at')

    # Get pending complaints
    complaints = Complaint.objects.filter(status='pending').order_by('-created_at')

    # Get total students
    total_students = CustomUser.objects.filter(is_active=True, role='student').count()

    # Get total fees
    total_fees = Fee.objects.count()
    unread_alerts = Notification.objects.filter(recipient=request.user, is_read=False).count()

    recent_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:5]
    recent_conversations = Conversation.objects.filter(participants=request.user).order_by('-updated_at')[:5]

    context = {
        'pending_registrations': pending_registrations,
        'complaints': complaints,
        'total_students': total_students,
        'total_fees': total_fees,
        'unread_alerts': unread_alerts,
        'recent_notifications': recent_notifications,
        'recent_conversations': recent_conversations,
    }

    return render(request, 'warden_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    pending_registrations = CustomUser.objects.filter(is_active=False, role='student').order_by('-created_at')
    recent_notifications = Notification.objects.filter(recipient=request.user).order_by('-created_at')[:5]
    recent_conversations = Conversation.objects.filter(participants=request.user).order_by('-updated_at')[:5]
    total_students = CustomUser.objects.filter(role='student').count()
    active_students = CustomUser.objects.filter(is_active=True, role='student').count()
    total_wardens = CustomUser.objects.filter(role='warden').count()
    unread_alerts = Notification.objects.filter(recipient=request.user, is_read=False).count()

    context = {
        'pending_registrations': pending_registrations,
        'pending_count': pending_registrations.count(),
        'total_students': total_students,
        'active_students': active_students,
        'total_wardens': total_wardens,
        'unread_alerts': unread_alerts,
        'recent_notifications': recent_notifications,
        'recent_conversations': recent_conversations,
    }

    return render(request, 'admin_dashboard.html', context)


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
        bulk_action = request.POST.get('bulk_action')
        leave_ids = request.POST.getlist('leave_ids') or [request.POST.get('leave_id')]
        action = request.POST.get('action') or bulk_action
        notes = request.POST.get('notes', '').strip()
        warden_profile, _ = WardenProfile.objects.get_or_create(user=request.user)

        processed = 0
        for raw_leave_id in leave_ids:
            if not raw_leave_id:
                continue
            try:
                leave = LeaveApplication.objects.get(id=raw_leave_id, status='pending')
            except LeaveApplication.DoesNotExist:
                continue

            leave.approved_by = warden_profile
            leave.approval_notes = notes or leave.approval_notes
            if action == 'approve':
                leave.status = 'approved'
                dispatch_status_notification(
                    recipient=leave.student.user,
                    title='Leave Approved',
                    message=f'Your leave request from {leave.leave_from} to {leave.leave_to} has been approved.',
                    notification_type='success',
                    sender=request.user,
                    related_model='leave',
                    related_id=leave.id
                )
            elif action == 'reject':
                leave.status = 'rejected'
                dispatch_status_notification(
                    recipient=leave.student.user,
                    title='Leave Rejected',
                    message=f'Your leave request from {leave.leave_from} to {leave.leave_to} has been rejected.',
                    notification_type='error',
                    sender=request.user,
                    related_model='leave',
                    related_id=leave.id
                )
            else:
                messages.error(request, 'Invalid action.')
                return redirect('warden_leave_requests')

            leave.save()
            processed += 1

        if processed:
            if action == 'approve':
                messages.success(request, f'{processed} leave request(s) approved.')
            elif action == 'reject':
                messages.success(request, f'{processed} leave request(s) rejected.')
        else:
            messages.error(request, 'No pending leave request(s) were selected.')

        return redirect('warden_leave_requests')

    return render(request, 'warden/leave_requests.html', {'leave_requests': leave_requests})


@login_required
@user_passes_test(is_warden)
def review_leave_application(request, leave_id):
    leave = get_object_or_404(LeaveApplication, id=leave_id)

    if request.method == 'POST':
        action = request.POST.get('action')
        notes = request.POST.get('notes', '').strip()
        warden_profile, _ = WardenProfile.objects.get_or_create(user=request.user)

        if action == 'approve':
            leave.status = 'approved'
            leave.approved_by = warden_profile
            leave.approval_notes = notes
            leave.save()
            dispatch_status_notification(
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
            leave.approved_by = warden_profile
            leave.approval_notes = notes
            leave.save()
            dispatch_status_notification(
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
def warden_attendance_analytics(request):
    today = datetime.now().date()
    last_7_days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    total_students = CustomUser.objects.filter(role='student', is_active=True).count()
    trend = []

    for day in last_7_days:
        present_count = Attendance.objects.filter(date=day, status='present').count()
        absent_count = Attendance.objects.filter(date=day, status='absent').count()
        late_count = Attendance.objects.filter(date=day, status='late').count()
        leave_count = Attendance.objects.filter(date=day, status='leave').count()
        rate = round((present_count / total_students) * 100, 1) if total_students else 0
        trend.append({
            'date': day,
            'label': day.strftime('%a'),
            'present': present_count,
            'absent': absent_count,
            'late': late_count,
            'leave': leave_count,
            'rate': rate,
        })

    absentee_students = []
    for student_user in CustomUser.objects.filter(role='student', is_active=True).select_related('student_profile').order_by('username'):
        profile = getattr(student_user, 'student_profile', None)
        if not profile:
            continue

        record = Attendance.objects.filter(student=profile, date=today).first()
        if record and record.status == 'absent':
            absentee_students.append({
                'name': student_user.get_full_name() or student_user.username,
                'status': record.get_status_display(),
                'date': record.date,
            })
        elif not record:
            absentee_students.append({
                'name': student_user.get_full_name() or student_user.username,
                'status': 'Unmarked',
                'date': today,
            })

    total_present = sum(item['present'] for item in trend)
    overall_rate = round((total_present / (total_students * len(trend))) * 100, 1) if total_students and trend else 0

    context = {
        'trend': trend,
        'absentees': absentee_students,
        'absentees_count': len(absentee_students),
        'total_students': total_students,
        'overall_rate': overall_rate,
        'today': today,
    }

    return render(request, 'warden/attendance_analytics.html', context)


@login_required
@user_passes_test(is_warden)
def warden_visitors(request):
    visitors = Visitor.objects.filter(status__in=['pending', 'approved', 'checked_in']).order_by('-visit_date', '-visit_time')
    context = {
        'visitors': visitors,
        'status_choices': Visitor.STATUS_CHOICES,
    }
    return render(request, 'warden/visitors.html', context)


@login_required
@user_passes_test(is_warden)
def visitor_gate_pass(request, visitor_id):
    visitor = get_object_or_404(Visitor, id=visitor_id)
    is_checked_in = visitor.status in ['checked_in', 'checked_out']
    context = {
        'visitor': visitor,
        'is_checked_in': is_checked_in,
    }
    return render(request, 'warden/visitor_gate_pass.html', context)


@login_required
@user_passes_test(is_warden)
def check_in_visitor(request, visitor_id):
    visitor = get_object_or_404(Visitor, id=visitor_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '').strip()
        warden_profile, _ = WardenProfile.objects.get_or_create(user=request.user)

        if new_status in ['approved', 'checked_in', 'checked_out', 'rejected']:
            visitor.status = new_status
            if new_status == 'checked_in':
                visitor.checked_in_at = timezone.now()
            if new_status == 'checked_out':
                visitor.checked_out_at = timezone.now()
            visitor.approved_by = warden_profile
            visitor.save()

            dispatch_status_notification(
                recipient=visitor.student.user,
                title='Visitor Gate Pass Update',
                message=f"Visitor {visitor.visitor_name} status updated to {visitor.get_status_display()}. {notes if notes else ''}".strip(),
                notification_type='success' if new_status in ['approved', 'checked_in'] else 'info',
                sender=request.user,
                related_model='visitor',
                related_id=visitor.id,
            )
            messages.success(request, 'Visitor status updated successfully.')
            return redirect('warden_visitors')

        messages.error(request, 'Invalid visitor status.')
        return redirect('warden_visitors')

    return redirect('visitor_gate_pass', visitor_id=visitor.id)


@login_required
@user_passes_test(is_warden)
def warden_complaints(request):
    complaints = Complaint.objects.filter(status='pending').order_by('-priority', '-created_at')

    if request.method == 'POST':
        bulk_action = request.POST.get('bulk_action')
        complaint_ids = request.POST.getlist('complaint_ids') or [request.POST.get('complaint_id')]
        warden_profile, _ = WardenProfile.objects.get_or_create(user=request.user)
        notes = request.POST.get('resolution_notes', '').strip()
        processed = 0

        for raw_complaint_id in complaint_ids:
            if not raw_complaint_id:
                continue
            try:
                complaint = Complaint.objects.get(id=raw_complaint_id, status='pending')
            except Complaint.DoesNotExist:
                continue

            complaint.resolved_by = warden_profile
            complaint.resolved_at = timezone.now()
            complaint.resolution_notes = notes or complaint.resolution_notes
            if bulk_action == 'resolve':
                complaint.status = 'resolved'
                dispatch_status_notification(
                    recipient=complaint.student.user,
                    title=f"Complaint Resolved: {complaint.title}",
                    message=f"Your complaint '{complaint.title}' has been resolved. {complaint.resolution_notes or ''}".strip(),
                    notification_type='success',
                    sender=request.user,
                    related_model='complaint',
                    related_id=complaint.id,
                )
            elif bulk_action == 'reject':
                complaint.status = 'rejected'
                dispatch_status_notification(
                    recipient=complaint.student.user,
                    title=f"Complaint Rejected: {complaint.title}",
                    message=f"Your complaint '{complaint.title}' has been rejected. {complaint.resolution_notes or ''}".strip(),
                    notification_type='warning',
                    sender=request.user,
                    related_model='complaint',
                    related_id=complaint.id,
                )
            else:
                messages.error(request, 'Invalid bulk action.')
                return redirect('warden_complaints')

            complaint.save()
            processed += 1

        if processed:
            if bulk_action == 'resolve':
                messages.success(request, f'{processed} complaint(s) resolved successfully.')
            elif bulk_action == 'reject':
                messages.success(request, f'{processed} complaint(s) rejected successfully.')
        else:
            messages.error(request, 'No pending complaint(s) were selected.')

        return redirect('warden_complaints')

    context = {
        'complaints': complaints,
        'status_choices': Complaint.STATUS_CHOICES,
    }

    return render(request, 'warden/complaints.html', context)


@login_required
@user_passes_test(is_warden)
def resolve_complaint(request, complaint_id):
    complaint = get_object_or_404(Complaint, id=complaint_id)
    warden_profile, _ = WardenProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = ComplaintResolutionForm(request.POST, instance=complaint)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.resolved_by = warden_profile
            complaint.resolved_at = timezone.now()
            complaint.save()

            # Create notification for the student
            dispatch_status_notification(
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


# ==================== CHAT VIEWS ====================

@login_required
def chat_view(request):
    conversations = Conversation.objects.filter(participants=request.user).order_by('-updated_at')
    selected_conversation = None
    thread_messages = []

    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            if not conversations.exists():
                conversation = Conversation.objects.create(title='Community Chat')
                conversation.participants.add(request.user)
            else:
                conversation = conversations.first()

            ChatMessage.objects.create(conversation=conversation, sender=request.user, content=content)
            conversation.save(update_fields=['updated_at'])
            messages.success(request, 'Message sent')
            return redirect(f"{reverse('chat')}?conversation={conversation.id}")

    conversation_id = request.GET.get('conversation')
    if conversation_id:
        selected_conversation = get_object_or_404(Conversation, id=conversation_id)
        if request.user not in selected_conversation.participants.all():
            selected_conversation = None
        else:
            thread_messages = list(selected_conversation.messages.select_related('sender').all())

    if not selected_conversation and conversations.exists():
        selected_conversation = conversations.first()
        thread_messages = list(selected_conversation.messages.select_related('sender').all())

    if not selected_conversation:
        selected_conversation = Conversation.objects.create(title='Community Chat')
        selected_conversation.participants.add(request.user)
        thread_messages = []

    unread_count = 0
    if selected_conversation:
        unread_count = selected_conversation.messages.filter(is_read=False).exclude(sender=request.user).count()
        if unread_count:
            selected_conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    context = {
        'conversations': conversations,
        'selected_conversation': selected_conversation,
        'messages': thread_messages,
        'unread_count': unread_count,
    }
    return render(request, 'chat.html', context)


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
                    dispatch_status_notification(
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