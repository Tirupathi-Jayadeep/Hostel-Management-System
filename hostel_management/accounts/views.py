from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from core.models import RoomAllocation
from operations.models import Complaint, Fee
from operations.forms import ComplaintForm


def login_view(request):

    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Role-based redirect
            if user.role == 'student':
                return redirect('student_dashboard')

            elif user.role == 'warden':
                return redirect('warden_dashboard')

            elif user.role == 'admin':
                return redirect('/admin')

        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')


def logout_view(request):
    logout(request)
    return redirect('login')


def student_dashboard(request):
    student = request.user.studentprofile

    room = RoomAllocation.objects.filter(student=student).first()
    complaints = Complaint.objects.filter(student=student)
    fee = Fee.objects.filter(student=student).first()

    return render(request, 'student_dashboard.html', {
        'student': student,
        'room': room,
        'complaints': complaints,
        'fee': fee
    })

def warden_dashboard(request):
    complaints = Complaint.objects.filter(status='pending')

    return render(request, 'warden_dashboard.html', {
        'complaints': complaints
    })

def add_complaint(request):
    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.student = request.user.studentprofile
            complaint.save()
            return redirect('student_dashboard')
    else:
        form = ComplaintForm()

    return render(request, 'add_complaint.html', {'form': form})