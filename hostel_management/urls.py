"""
URL configuration for hostel_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import logout
from django.shortcuts import redirect
import types


def _admin_login_override(self, request, extra_context=None):
    if request.user.is_authenticated and not request.user.is_staff:
        logout(request)
        return redirect('login')
    return admin.AdminSite.login(self, request, extra_context)

admin.site.login = types.MethodType(_admin_login_override, admin.site)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('accounts.urls')),
]