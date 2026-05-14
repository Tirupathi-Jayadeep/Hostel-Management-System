from django.contrib import admin
from .models import Complaint, Attendance,Fee

admin.site.register(Complaint)
admin.site.register(Attendance)
admin.site.register(Fee)