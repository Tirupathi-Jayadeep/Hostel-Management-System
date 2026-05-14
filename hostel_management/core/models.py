from django.db import models

class Room(models.Model):

    room_number = models.CharField(max_length=10)
    floor = models.IntegerField()
    capacity = models.IntegerField()

    def __str__(self):
        return self.room_number
from django.db import models
from accounts.models import StudentProfile

class RoomAllocation(models.Model):

    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE)
    room = models.ForeignKey(Room, on_delete=models.CASCADE)

    allocated_on = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.user.username} -> {self.room.room_number}"