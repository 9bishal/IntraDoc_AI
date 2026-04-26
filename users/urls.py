"""
URL configuration for the users app.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    ProfileView,
    AccessTokenCreateView,
    AccessTokenVerifyView,
    OTPVerifyView,
    FirebaseLoginView,
    ForgotPasswordView,
    ResetPasswordView,
)

app_name = 'users'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('verify-token', AccessTokenVerifyView.as_view(), name='verify-token'),
    path('verify-otp', OTPVerifyView.as_view(), name='verify-otp'),
    path('firebase-login', FirebaseLoginView.as_view(), name='firebase-login'),
    path('forgot-password', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password', ResetPasswordView.as_view(), name='reset-password'),
    path('access-tokens/create/', AccessTokenCreateView.as_view(), name='access-token-create'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
]
