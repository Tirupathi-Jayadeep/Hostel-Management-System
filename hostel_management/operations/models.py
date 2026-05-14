from django.db import models
from accounts.models import StudentProfile

class Complaint(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('resolved', 'Resolved'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)

    title = models.CharField(max_length=100)

    description = models.TextField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
class Attendance(models.Model):

    STATUS_CHOICES = (
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('leave', 'Leave'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)

    date = models.DateField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES)

    def __str__(self):
        return f"{self.student.user.username} - {self.date}"
class Fee(models.Model):

    STATUS_CHOICES = (
        ('paid', 'Paid'),
        ('pending', 'Pending'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)

    amount = models.DecimalField(max_digits=10, decimal_places=2)

    due_date = models.DateField()

    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"{self.student.user.username} - {self.status}"