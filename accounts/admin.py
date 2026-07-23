from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import CustomUser, StudentProfile, WardenProfile


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'phone_number', 'profile_picture', 'last_login_ip', 'created_at')
        }),
    )
    list_display = ('username', 'email', 'first_name', 'role_badge', 'phone_number', 'is_active', 'last_login')
    list_filter = ('role', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'phone_number')
    readonly_fields = ('last_login_ip', 'created_at', 'last_login')

    def role_badge(self, obj):
        colors = {
            'admin': '#e74c3c',
            'warden': '#f39c12',
            'student': '#3498db'
        }
        color = colors.get(obj.role, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color,
            obj.get_role_display()
        )
    role_badge.short_description = 'Role'


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'enrollment_number', 'contact_number', 'gender', 'blood_group', 'is_active')
    list_filter = ('is_active', 'gender', 'blood_group')
    search_fields = ('enrollment_number', 'user__username', 'contact_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('enrollment_number', 'date_of_birth', 'gender', 'blood_group', 'contact_number')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_number', 'parent_contact')
        }),
        ('Medical', {
            'fields': ('medical_conditions',)
        }),
        ('Room Preferences', {
            'fields': ('room_preference', 'roommate_preference')
        }),
        ('Documents', {
            'fields': ('id_proof', 'vaccination_certificate', 'admission_letter')
        }),
        ('Status', {
            'fields': ('is_active', 'checkin_date', 'checkout_date')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def student_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
    student_name.short_description = 'Name'


@admin.register(WardenProfile)
class WardenProfileAdmin(admin.ModelAdmin):
    list_display = ('warden_name', 'assigned_floor', 'office_location', 'is_available')
    list_filter = ('is_available', 'assigned_floor')
    search_fields = ('user__username', 'office_contact')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Assignment', {
            'fields': ('assigned_floor', 'assigned_blocks', 'department')
        }),
        ('Professional', {
            'fields': ('qualification', 'experience_years')
        }),
        ('Contact', {
            'fields': ('office_location', 'office_contact', 'availability_hours')
        }),
        ('Status', {
            'fields': ('is_available',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def warden_name(self, obj):
        return f"{obj.user.first_name} {obj.user.last_name}".strip() or obj.user.username
    warden_name.short_description = 'Name'