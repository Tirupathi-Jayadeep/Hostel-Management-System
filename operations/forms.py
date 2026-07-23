from django import forms
from .models import Complaint, Visitor, LeaveApplication, MaintenanceRequest, Announcement, Event, RoomRating


class ComplaintForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['title', 'description', 'category', 'priority', 'room_number', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Brief title of the complaint'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Detailed description'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 101'}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }


class ComplaintResolutionForm(forms.ModelForm):
    class Meta:
        model = Complaint
        fields = ['status', 'resolution_notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'resolution_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class VisitorForm(forms.ModelForm):
    class Meta:
        model = Visitor
        fields = ['visitor_name', 'visitor_phone', 'visitor_id_type', 'visitor_id_number', 'visit_date', 'visit_time', 'purpose']
        widgets = {
            'visitor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'visitor_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'visitor_id_type': forms.Select(attrs={'class': 'form-control'}),
            'visitor_id_number': forms.TextInput(attrs={'class': 'form-control'}),
            'visit_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'visit_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'purpose': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Purpose of visit'}),
        }


class LeaveApplicationForm(forms.ModelForm):
    class Meta:
        model = LeaveApplication
        fields = ['leave_from', 'leave_to', 'reason', 'destination', 'contact_during_leave']
        widgets = {
            'leave_from': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'leave_to': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'reason': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'destination': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Where will you be going?'}),
            'contact_during_leave': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number during leave'}),
        }


class MaintenanceRequestForm(forms.ModelForm):
    class Meta:
        model = MaintenanceRequest
        fields = ['room_number', 'category', 'priority', 'title', 'description', 'attachment']
        widgets = {
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 101'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'attachment': forms.FileInput(attrs={'class': 'form-control'}),
        }


class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'content', 'priority', 'visibility', 'floor_block', 'pinned']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'visibility': forms.Select(attrs={'class': 'form-control'}),
            'floor_block': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Floor 1, Block A'}),
            'pinned': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = [
            'title', 'description', 'location', 'event_date', 'event_time',
            'organizer', 'contact_person', 'contact_number', 'is_mandatory',
            'max_attendees', 'registration_required', 'poster'
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'event_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'event_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'organizer': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'is_mandatory': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_attendees': forms.NumberInput(attrs={'class': 'form-control'}),
            'registration_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'poster': forms.FileInput(attrs={'class': 'form-control'}),
        }


class RoomRatingForm(forms.ModelForm):
    class Meta:
        model = RoomRating
        fields = ['room_number', 'cleanliness_rating', 'maintenance_rating', 'space_rating', 'ventilation_rating', 'overall_rating', 'comments']
        widgets = {
            'room_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'cleanliness_rating': forms.RadioSelect(choices=RoomRating.RATING_CHOICES),
            'maintenance_rating': forms.RadioSelect(choices=RoomRating.RATING_CHOICES),
            'space_rating': forms.RadioSelect(choices=RoomRating.RATING_CHOICES),
            'ventilation_rating': forms.RadioSelect(choices=RoomRating.RATING_CHOICES),
            'overall_rating': forms.RadioSelect(choices=RoomRating.RATING_CHOICES),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }