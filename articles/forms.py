"""
Forms for the News Application.

Handles user registration using a custom user model
with role-based assignment.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User


class CustomUserCreationForm(UserCreationForm):
    """
    Custom user registration form.

    Extends Django's default UserCreationForm to include:
    - email field
    - role selection (Reader, Journalist, Editor)
    """

    class Meta:
        model = User
        fields = ("username", "email", "role")

    def save(self, commit=True):
        """
        Creates a new user instance with a hashed password.

        Ensures password is properly encrypted before saving.
        """
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])

        if commit:
            user.save()

        return user
