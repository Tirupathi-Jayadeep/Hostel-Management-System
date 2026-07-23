from django.contrib import admin
from django.utils.html import format_html
from .models import Room, RoomAllocation, RoomConditionReport


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'floor', 'room_type', 'capacity', 'current_occupancy', 'status_badge', 'last_maintenance')
    list_filter = ('status', 'room_type', 'floor', 'has_ac', 'has_wifi')
    search_fields = ('room_number', 'block')
    readonly_fields = ('created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('room_number', 'floor', 'block', 'room_type', 'capacity')
        }),
        ('Physical Details', {
            'fields': ('area_sqft', 'rent_amount', 'amenities')
        }),
        ('Amenities', {
            'fields': ('has_ac', 'has_wifi', 'has_attached_bathroom', 'has_balcony')
        }),
        ('Status', {
            'fields': ('is_available', 'status', 'last_maintenance', 'maintenance_notes')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'available': '#27ae60',
            'occupied': '#3498db',
            'maintenance': '#f39c12',
            'closed': '#e74c3c'
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(RoomAllocation)
class RoomAllocationAdmin(admin.ModelAdmin):
    list_display = ('student', 'room', 'allocated_on', 'scheduled_checkout', 'is_active')
    list_filter = ('is_active', 'allocated_on')
    search_fields = ('student__user__username', 'room__room_number')
    readonly_fields = ('allocated_on', 'is_active')
    
    fieldsets = (
        ('Allocation', {
            'fields': ('student', 'room')
        }),
        ('Timeline', {
            'fields': ('allocated_on', 'allocated_by', 'scheduled_checkout', 'actual_checkout')
        }),
        ('Additional', {
            'fields': ('notes', 'is_active')
        }),
    )


@admin.register(RoomConditionReport)
class RoomConditionReportAdmin(admin.ModelAdmin):
    list_display = ('room', 'overall_condition_badge', 'inspection_date', 'inspected_by')
    list_filter = ('overall_condition', 'inspection_date')
    search_fields = ('room__room_number', 'inspected_by')
    readonly_fields = ('inspection_date',)
    
    fieldsets = (
        ('Room', {
            'fields': ('room',)
        }),
        ('Condition Assessment', {
            'fields': ('overall_condition', 'walls_condition', 'flooring_condition', 'furniture_condition', 'plumbing_condition', 'electrical_condition')
        }),
        ('Report', {
            'fields': ('issues', 'recommendations')
        }),
        ('Details', {
            'fields': ('inspected_by', 'inspection_date')
        }),
    )
    
    def overall_condition_badge(self, obj):
        colors = {
            'excellent': '#27ae60',
            'good': '#2ecc71',
            'fair': '#f39c12',
            'poor': '#e74c3c',
            'critical': '#c0392b'
        }
        color = colors.get(obj.overall_condition, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 5px 10px; border-radius: 5px;">{}</span>',
            color,
            obj.get_overall_condition_display()
        )
    overall_condition_badge.short_description = 'Overall Condition'