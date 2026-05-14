from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):

    ROLE_CHOICES = (
        ('admin', 'Admin'),
        ('warden', 'Warden'),
        ('student', 'Student'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
class StudentProfile(models.Model):

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    enrollment_number = models.CharField(max_length=20)
    contact_number = models.CharField(max_length=15)

    def __str__(self):
        return self.user.username
class WardenProfile(models.Model):

    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)

    assigned_floor = models.IntegerField()

    def __str__(self):
        return self.user.username