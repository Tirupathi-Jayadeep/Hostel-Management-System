from django.db import models
from accounts.models import StudentProfile


class Room(models.Model):
    ROOM_TYPE_CHOICES = (
        ('single', 'Single Occupancy'),
        ('double', 'Double Occupancy'),
        ('triple', 'Triple Occupancy'),
        ('quad', 'Quad Occupancy'),
    )

    AMENITIES_CHOICES = (
        ('ac', 'Air Conditioner'),
        ('wifi', 'WiFi'),
        ('attached_bathroom', 'Attached Bathroom'),
        ('balcony', 'Balcony'),
        ('study_table', 'Study Table'),
        ('wardrobe', 'Wardrobe'),
    )

    room_number = models.CharField(max_length=10, unique=True)
    floor = models.IntegerField()
    block = models.CharField(max_length=20, blank=True, help_text="e.g., A, B, C")
    
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES, default='double')
    capacity = models.IntegerField()
    
    area_sqft = models.FloatField(blank=True, null=True)
    rent_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
    amenities = models.CharField(
        max_length=200,
        blank=True,
        help_text="Comma-separated list or use checkboxes below"
    )
    has_ac = models.BooleanField(default=False)
    has_wifi = models.BooleanField(default=False)
    has_attached_bathroom = models.BooleanField(default=False)
    has_balcony = models.BooleanField(default=False)
    
    is_available = models.BooleanField(default=True)
    status = models.CharField(
        max_length=20,
        choices=(
            ('available', 'Available'),
            ('occupied', 'Occupied'),
            ('maintenance', 'Under Maintenance'),
            ('closed', 'Closed'),
        ),
        default='available'
    )
    
    last_maintenance = models.DateField(blank=True, null=True)
    maintenance_notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Room {self.room_number} - Floor {self.floor}"

    @property
    def current_occupancy(self):
        return self.allocations.count()

    @property
    def available_beds(self):
        return self.capacity - self.current_occupancy

    class Meta:
        ordering = ['floor', 'room_number']
        indexes = [
            models.Index(fields=['room_number']),
            models.Index(fields=['floor']),
            models.Index(fields=['status']),
        ]


class RoomAllocation(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE, related_name='room_allocation')
    room = models.ForeignKey(Room, on_delete=models.PROTECT, related_name='allocations')
    
    allocated_on = models.DateField(auto_now_add=True)
    allocated_by = models.CharField(max_length=100, blank=True)
    
    scheduled_checkout = models.DateField(blank=True, null=True)
    actual_checkout = models.DateField(blank=True, null=True)
    
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.student.user.username} -> {self.room.room_number}"

    class Meta:
        ordering = ['-allocated_on']
        indexes = [
            models.Index(fields=['room']),
            models.Index(fields=['is_active']),
        ]


class RoomConditionReport(models.Model):
    CONDITION_CHOICES = (
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('critical', 'Critical'),
    )

    room = models.ForeignKey(Room, on_delete=models.CASCADE, related_name='condition_reports')
    
    overall_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES)
    walls_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True)
    flooring_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True)
    furniture_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True)
    plumbing_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True)
    electrical_condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, blank=True)
    
    issues = models.TextField(blank=True, help_text="List of issues found")
    recommendations = models.TextField(blank=True)
    
    inspected_by = models.CharField(max_length=100)
    inspection_date = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Inspection of {self.room.room_number} - {self.inspection_date}"

    class Meta:
        ordering = ['-inspection_date']