from django.urls import path
from .views import add_complaint, login_view, logout_view, student_dashboard, warden_dashboard

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('student/', student_dashboard, name='student_dashboard'),
    path('warden/', warden_dashboard, name='warden_dashboard'),
    path('add-complaint/', add_complaint, name='add_complaint'),
]