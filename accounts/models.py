from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class CustomUser(AbstractUser):

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('warden', 'Warden'),
        ('student', 'Student'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format '+999999999'.")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def unread_notifications_count(self):
        return self.notifications.filter(is_read=False).count()

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['role']),
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
        ]


class StudentProfile(models.Model):
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    )

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    enrollment_number = models.CharField(max_length=20, unique=True)
    contact_number = models.CharField(max_length=15, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True)
    
    # Emergency contact information
    emergency_contact_name = models.CharField(max_length=100, blank=True)
    emergency_contact_number = models.CharField(max_length=15, blank=True)
    parent_contact = models.CharField(max_length=15, blank=True)
    
    # Medical information
    blood_group = models.CharField(max_length=5, blank=True)
    medical_conditions = models.TextField(blank=True, help_text="Any medical conditions or allergies")
    
    # Room preferences
    room_preference = models.CharField(max_length=100, blank=True, help_text="Room type preference (e.g., AC, WiFi)")
    roommate_preference = models.CharField(max_length=100, blank=True, help_text="Preferences for roommates")
    
    # Document uploads
    id_proof = models.FileField(upload_to='id_proofs/', blank=True, null=True)
    vaccination_certificate = models.FileField(upload_to='vaccination/', blank=True, null=True)
    admission_letter = models.FileField(upload_to='admission_letters/', blank=True, null=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    checkin_date = models.DateField(blank=True, null=True)
    checkout_date = models.DateField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} - {self.enrollment_number}"

    class Meta:
        ordering = ['enrollment_number']
        indexes = [
            models.Index(fields=['enrollment_number']),
            models.Index(fields=['user']),
        ]


class WardenProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='warden_profile')
    assigned_floor = models.IntegerField(blank=True, null=True)
    assigned_blocks = models.CharField(max_length=100, blank=True, help_text="Comma-separated block assignments")
    department = models.CharField(max_length=100, blank=True)
    qualification = models.CharField(max_length=100, blank=True)
    experience_years = models.IntegerField(default=0)
    office_location = models.CharField(max_length=100, blank=True)
    office_contact = models.CharField(max_length=15, blank=True)
    is_available = models.BooleanField(default=True)
    availability_hours = models.CharField(max_length=100, blank=True, help_text="e.g., 9 AM to 5 PM")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.username} (Warden - Floor {self.assigned_floor})"

    class Meta:
        ordering = ['assigned_floor']
        indexes = [
            models.Index(fields=['assigned_floor']),
        ]