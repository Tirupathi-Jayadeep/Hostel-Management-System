from django.db import models
from django.contrib.auth.models import User
from accounts.models import StudentProfile, WardenProfile, CustomUser
from django.utils import timezone
from django.core.validators import MinValueValidator


class Complaint(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
        ('rejected', 'Rejected'),
    )

    CATEGORY_CHOICES = (
        ('room', 'Room Issues'),
        ('water', 'Water/Sanitation'),
        ('electricity', 'Electricity'),
        ('maintenance', 'Maintenance'),
        ('food', 'Food/Mess'),
        ('other', 'Other'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='complaints')
    warden = models.ForeignKey(WardenProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_complaints')

    title = models.CharField(max_length=100)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')

    attachment = models.FileField(upload_to='complaint_attachments/', blank=True, null=True)
    room_number = models.CharField(max_length=20, blank=True)

    resolution_notes = models.TextField(blank=True)
    resolved_by = models.ForeignKey(WardenProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='resolved_complaints')

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.status}"

    @property
    def is_editable(self):
        return self.status in ['pending', 'in_progress']

    def mark_resolved(self):
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['student']),
        ]


class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('leave', 'Leave'),
        ('late', 'Late'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendance')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    
    checkin_time = models.TimeField(blank=True, null=True)
    checkout_time = models.TimeField(blank=True, null=True)
    notes = models.TextField(blank=True)
    recorded_by = models.ForeignKey(WardenProfile, on_delete=models.SET_NULL, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.date} ({self.status})"

    class Meta:
        unique_together = ('student', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['student']),
        ]


class Fee(models.Model):
    STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('overdue', 'Overdue'),
        ('partial', 'Partially Paid'),
        ('waived', 'Waived'),
    )

    FEE_TYPE_CHOICES = (
        ('hostel', 'Hostel Fee'),
        ('mess', 'Mess Fee'),
        ('maintenance', 'Maintenance Fee'),
        ('electricity', 'Electricity Fee'),
        ('registration', 'Registration Fee'),
        ('other', 'Other'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='fees')
    
    fee_type = models.CharField(max_length=20, choices=FEE_TYPE_CHOICES, default='hostel')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    
    due_date = models.DateField()
    paid_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    month = models.CharField(max_length=20, blank=True, help_text="Month for monthly fees (e.g., Jan-2024)")
    description = models.TextField(blank=True)
    receipt_number = models.CharField(max_length=50, blank=True, null=True, unique=True)
    
    payment_method = models.CharField(
        max_length=20,
        choices=(
            ('cash', 'Cash'),
            ('check', 'Check'),
            ('transfer', 'Bank Transfer'),
            ('card', 'Card'),
            ('online', 'Online Payment'),
        ),
        blank=True
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.fee_type} ({self.status})"

    @property
    def pending_amount(self):
        return self.amount - self.amount_paid

    class Meta:
        ordering = ['-due_date']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['student']),
            models.Index(fields=['due_date']),
        ]


class Visitor(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('rejected', 'Rejected'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='visitors')
    
    visitor_name = models.CharField(max_length=100)
    visitor_phone = models.CharField(max_length=15)
    visitor_id_type = models.CharField(
        max_length=20,
        choices=(
            ('aadhar', 'Aadhar'),
            ('pan', 'PAN'),
            ('license', 'License'),
            ('passport', 'Passport'),
            ('other', 'Other'),
        ),
        default='aadhar'
    )
    visitor_id_number = models.CharField(max_length=50)
    
    visit_date = models.DateField()
    visit_time = models.TimeField()
    purpose = models.CharField(max_length=200)
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_out_at = models.DateTimeField(null=True, blank=True)
    
    approved_by = models.ForeignKey(WardenProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_visitors')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.visitor_name} - {self.student.user.username}"

    class Meta:
        ordering = ['-visit_date']
        indexes = [
            models.Index(fields=['visit_date']),
            models.Index(fields=['student']),
        ]


class LeaveApplication(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='leave_applications')
    
    leave_from = models.DateField()
    leave_to = models.DateField()
    reason = models.TextField()
    destination = models.CharField(max_length=200, blank=True)
    contact_during_leave = models.CharField(max_length=15)
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    approved_by = models.ForeignKey(WardenProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_leaves')
    approval_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.user.username} - {self.leave_from} to {self.leave_to}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['student']),
        ]


class MaintenanceRequest(models.Model):
    PRIORITY_CHOICES = (
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )

    CATEGORY_CHOICES = (
        ('plumbing', 'Plumbing'),
        ('electrical', 'Electrical'),
        ('carpentry', 'Carpentry'),
        ('cleaning', 'Cleaning'),
        ('hvac', 'HVAC'),
        ('other', 'Other'),
    )

    student_or_room = models.CharField(max_length=100)
    room_number = models.CharField(max_length=20, blank=True)
    
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='other')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    title = models.CharField(max_length=150)
    description = models.TextField()
    
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.CharField(max_length=100, blank=True)
    
    estimated_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    actual_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    attachment = models.FileField(upload_to='maintenance_attachments/', blank=True, null=True)
    completion_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.title} - {self.status}"

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_at']),
        ]


class Announcement(models.Model):
    PRIORITY_CHOICES = (
        ('normal', 'Normal'),
        ('important', 'Important'),
        ('urgent', 'Urgent'),
    )

    TARGET_CHOICES = (
        ('all', 'All Users'),
        ('students', 'Students Only'),
        ('wardens', 'Wardens Only'),
        ('admins', 'Admins Only'),
    )

    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='normal')
    target_audience = models.CharField(max_length=20, choices=TARGET_CHOICES, default='all')
    visibility = models.CharField(
        max_length=20,
        choices=(
            ('all', 'All Students'),
            ('floor', 'Specific Floor'),
            ('block', 'Specific Block'),
        ),
        default='all'
    )
    floor_block = models.CharField(max_length=50, blank=True)

    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='announcements')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    is_active = models.BooleanField(default=True)
    expiry_date = models.DateTimeField(blank=True, null=True)
    is_pinned = models.BooleanField(default=False, help_text="Pinned announcements appear at the top")
    pinned = models.BooleanField(default=False)

    class Meta:
        ordering = ['-is_pinned', '-pinned', '-created_at']
        indexes = [
            models.Index(fields=['is_active']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"

    def is_expired(self):
        if self.expiry_date:
            return timezone.now() > self.expiry_date
        return False

    def is_visible_to_user(self, user):
        """Check if this announcement is visible to a specific user"""
        if not self.is_active or self.is_expired():
            return False

        if self.target_audience == 'all':
            return True
        elif self.target_audience == 'students' and user.role == 'student':
            return True
        elif self.target_audience == 'wardens' and user.role == 'warden':
            return True
        elif self.target_audience == 'admins' and user.role == 'admin':
            return True

        return False


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('error', 'Error'),
    )

    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES, default='info')

    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='notifications')
    sender = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='sent_notifications')

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional link to related object
    related_model = models.CharField(max_length=50, blank=True, help_text="Model name (e.g., 'complaint', 'fee')")
    related_id = models.PositiveIntegerField(blank=True, null=True, help_text="ID of related object")

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} -> {self.recipient.username}"

    def mark_as_read(self):
        self.is_read = True
        self.save()

    @classmethod
    def create_notification(cls, recipient, title, message, notification_type='info', sender=None, related_model='', related_id=None):
        """Helper method to create notifications"""
        return cls.objects.create(
            recipient=recipient,
            title=title,
            message=message,
            notification_type=notification_type,
            sender=sender,
            related_model=related_model,
            related_id=related_id
        )


class Conversation(models.Model):
    title = models.CharField(max_length=200, blank=True)
    participants = models.ManyToManyField(CustomUser, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return self.title or f'Conversation {self.id}'


class ChatMessage(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='chat_messages')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f'{self.sender.username}: {self.content[:40]}'


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200, blank=True)
    
    event_date = models.DateField()
    event_time = models.TimeField(blank=True, null=True)
    
    organizer = models.CharField(max_length=100, blank=True)
    contact_person = models.CharField(max_length=100, blank=True)
    contact_number = models.CharField(max_length=15, blank=True)
    
    is_mandatory = models.BooleanField(default=False)
    max_attendees = models.IntegerField(null=True, blank=True)
    registration_required = models.BooleanField(default=False)
    
    poster = models.ImageField(upload_to='event_posters/', blank=True, null=True)
    
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_events')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['event_date', 'event_time']
        indexes = [
            models.Index(fields=['event_date']),
        ]


class RoomRating(models.Model):
    RATING_CHOICES = (
        (1, '⭐ Poor'),
        (2, '⭐⭐ Fair'),
        (3, '⭐⭐⭐ Good'),
        (4, '⭐⭐⭐⭐ Very Good'),
        (5, '⭐⭐⭐⭐⭐ Excellent'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='room_ratings')
    room_number = models.CharField(max_length=20)
    
    cleanliness_rating = models.IntegerField(choices=RATING_CHOICES)
    maintenance_rating = models.IntegerField(choices=RATING_CHOICES)
    space_rating = models.IntegerField(choices=RATING_CHOICES)
    ventilation_rating = models.IntegerField(choices=RATING_CHOICES)
    
    overall_rating = models.IntegerField(choices=RATING_CHOICES)
    comments = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Rating for Room {self.room_number} by {self.student.user.username}"

    class Meta:
        ordering = ['-created_at']
        unique_together = ['student', 'room_number', ]