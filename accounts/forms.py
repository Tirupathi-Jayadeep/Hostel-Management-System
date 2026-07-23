from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from datetime import datetime
from .models import CustomUser, StudentProfile, WardenProfile


class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(max_length=17, required=False, help_text="Optional")
    enrollment_number = forms.CharField(max_length=20, required=True, help_text="Your university enrollment number")

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'enrollment_number', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = 'Password must contain at least 8 characters, including uppercase, lowercase, and numbers'
        self.fields['username'].help_text = 'Choose a unique username'

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def clean_enrollment_number(self):
        enrollment_number = self.cleaned_data.get('enrollment_number')
        if StudentProfile.objects.filter(enrollment_number=enrollment_number).exists():
            raise forms.ValidationError("This enrollment number is already registered.")
        return enrollment_number

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'student'  # Force student role for self-registration
        user.is_active = False  # Require admin approval
        if commit:
            user.save()
            # Create student profile with enrollment number
            StudentProfile.objects.create(
                user=user,
                enrollment_number=self.cleaned_data['enrollment_number']
            )
        return user


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'profile_picture')


class StudentProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            'enrollment_number', 'contact_number', 'date_of_birth', 'gender',
            'emergency_contact_name', 'emergency_contact_number', 'parent_contact',
            'blood_group', 'medical_conditions', 'room_preference', 'roommate_preference',
            'id_proof', 'vaccination_certificate', 'admission_letter'
        ]
        widgets = {
            'enrollment_number': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-control'}),
            'medical_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'room_preference': forms.TextInput(attrs={'class': 'form-control'}),
            'roommate_preference': forms.TextInput(attrs={'class': 'form-control'}),
            'id_proof': forms.FileInput(attrs={'class': 'form-control'}),
            'vaccination_certificate': forms.FileInput(attrs={'class': 'form-control'}),
            'admission_letter': forms.FileInput(attrs={'class': 'form-control'}),
        }


class StudentProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = [
            'contact_number', 'emergency_contact_name', 'emergency_contact_number',
            'parent_contact', 'blood_group', 'medical_conditions'
        ]
        widgets = {
            'contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_name': forms.TextInput(attrs={'class': 'form-control'}),
            'emergency_contact_number': forms.TextInput(attrs={'class': 'form-control'}),
            'parent_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-control'}),
            'medical_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class WardenProfileForm(forms.ModelForm):
    class Meta:
        model = WardenProfile
        fields = [
            'assigned_floor', 'assigned_blocks', 'department', 'qualification',
            'experience_years', 'office_location', 'office_contact', 'availability_hours'
        ]
        widgets = {
            'assigned_floor': forms.NumberInput(attrs={'class': 'form-control'}),
            'assigned_blocks': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.TextInput(attrs={'class': 'form-control'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control'}),
            'experience_years': forms.NumberInput(attrs={'class': 'form-control'}),
            'office_location': forms.TextInput(attrs={'class': 'form-control'}),
            'office_contact': forms.TextInput(attrs={'class': 'form-control'}),
            'availability_hours': forms.TextInput(attrs={'class': 'form-control'}),
        }


class CustomUserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'profile_picture']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.FileInput(attrs={'class': 'form-control'}),
        }


class AdminUserCreationForm(UserCreationForm):
    """Form for admin to create users with any role"""
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, required=True)
    phone_number = forms.CharField(max_length=17, required=False, help_text="Optional")
    is_staff = forms.BooleanField(required=False, help_text="Staff status for admin access")
    is_superuser = forms.BooleanField(required=False, help_text="Superuser status (full admin access)")

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone_number', 'role', 'is_staff', 'is_superuser', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].help_text = 'Password must contain at least 8 characters'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_active = True  # Ensure new admin-created users are active
        if commit:
            user.save()
            # Create appropriate profile based on role
            if user.role == 'student':
                StudentProfile.objects.get_or_create(
                    user=user,
                    defaults={'enrollment_number': f"ST-{user.id}-{datetime.now().year}"}
                )
            elif user.role == 'warden':
                WardenProfile.objects.get_or_create(
                    user=user,
                    defaults={'department': 'Hostel Management'}
                )
        return user
