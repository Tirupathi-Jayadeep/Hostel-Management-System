from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Complaint, Attendance, Fee, Visitor, LeaveApplication,
    MaintenanceRequest, Announcement, Event, RoomRating, Notification,
    Conversation, ChatMessage
)


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'category', 'priority_badge', 'status_badge', 'created_at')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('title', 'student__user__username', 'description')
    readonly_fields = ('created_at', 'updated_at', 'resolved_at')
    
    fieldsets = (
        ('Complaint Details', {
            'fields': ('student', 'title', 'description', 'category', 'priority', 'room_number', 'attachment')
        }),
        ('Resolution', {
            'fields': ('status', 'warden', 'resolved_by', 'resolution_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )
    
    def priority_badge(self, obj):
        colors = {
            'low': '#3498db',
            'medium': '#f39c12',
            'high': '#e74c3c',
            'critical': '#c0392b'
        }
        color = colors.get(obj.priority, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#3498db',
            'in_progress': '#f39c12',
            'resolved': '#27ae60',
            'closed': '#95a5a6',
            'rejected': '#e74c3c'
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'status_badge', 'checkin_time', 'recorded_by')
    list_filter = ('status', 'date')
    search_fields = ('student__user__username', 'date')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Attendance Info', {
            'fields': ('student', 'date', 'status', 'checkin_time', 'checkout_time', 'notes')
        }),
        ('Recording', {
            'fields': ('recorded_by', 'created_at', 'updated_at')
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'present': '#27ae60',
            'absent': '#e74c3c',
            'leave': '#f39c12',
            'late': '#3498db'
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(Fee)
class FeeAdmin(admin.ModelAdmin):
    list_display = ('student', 'fee_type', 'amount', 'status_badge', 'due_date', 'pending_amount')
    list_filter = ('status', 'fee_type', 'due_date')
    search_fields = ('student__user__username', 'receipt_number')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Fee Details', {
            'fields': ('student', 'fee_type', 'amount', 'month', 'description')
        }),
        ('Payment', {
            'fields': ('status', 'amount_paid', 'payment_method', 'receipt_number', 'due_date', 'paid_date')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'paid': '#27ae60',
            'pending': '#f39c12',
            'overdue': '#e74c3c',
            'partial': '#3498db',
            'waived': '#95a5a6'
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ('visitor_name', 'student', 'visit_date', 'status_badge', 'approved_by')
    list_filter = ('status', 'visit_date', 'visitor_id_type')
    search_fields = ('visitor_name', 'student__user__username', 'visitor_id_number')
    readonly_fields = ('created_at', 'updated_at')
    
    def status_badge(self, obj):
        colors = {
            'pending': '#3498db',
            'approved': '#27ae60',
            'checked_in': '#f39c12',
            'checked_out': '#95a5a6',
            'rejected': '#e74c3c'
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'leave_from', 'leave_to', 'status_badge', 'created_at')
    list_filter = ('status', 'leave_from')
    search_fields = ('student__user__username', 'destination')
    readonly_fields = ('created_at', 'updated_at')
    
    def status_badge(self, obj):
        colors = {
            'pending': '#3498db',
            'approved': '#27ae60',
            'rejected': '#e74c3c',
            'cancelled': '#95a5a6'
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(MaintenanceRequest)
class MaintenanceRequestAdmin(admin.ModelAdmin):
    list_display = ('title', 'room_number', 'category', 'priority_badge', 'status_badge', 'created_at')
    list_filter = ('status', 'priority', 'category', 'created_at')
    search_fields = ('title', 'room_number', 'description')
    readonly_fields = ('created_at', 'completed_at')
    
    def priority_badge(self, obj):
        colors = {
            'low': '#3498db',
            'medium': '#f39c12',
            'high': '#e74c3c',
            'urgent': '#c0392b'
        }
        color = colors.get(obj.priority, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'
    
    def status_badge(self, obj):
        colors = {
            'pending': '#3498db',
            'assigned': '#f39c12',
            'in_progress': '#e67e22',
            'completed': '#27ae60',
            'cancelled': '#95a5a6'
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title', 'priority_badge', 'is_active', 'pinned', 'created_at')
    list_filter = ('is_active', 'pinned', 'priority', 'created_at')
    search_fields = ('title', 'content')
    readonly_fields = ('created_at', 'updated_at')
    
    def priority_badge(self, obj):
        colors = {
            'normal': '#3498db',
            'important': '#f39c12',
            'urgent': '#e74c3c'
        }
        color = colors.get(obj.priority, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_badge.short_description = 'Priority'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('recipient', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('title', 'message', 'recipient__username')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_active')
    filter_horizontal = ('participants',)


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('content', 'sender__username')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_date', 'location', 'is_mandatory', 'registration_required')
    list_filter = ('event_date', 'is_mandatory', 'registration_required')
    search_fields = ('title', 'location', 'organizer')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(RoomRating)
class RoomRatingAdmin(admin.ModelAdmin):
    list_display = ('student', 'room_number', 'overall_rating_display', 'created_at')
    list_filter = ('overall_rating', 'room_number', 'created_at')
    search_fields = ('student__user__username', 'room_number')
    readonly_fields = ('created_at', 'updated_at')
    
    def overall_rating_display(self, obj):
        return f"{'⭐' * obj.overall_rating}"
    overall_rating_display.short_description = 'Rating'