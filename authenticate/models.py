from django.contrib.auth.models import AbstractUser
from django.db import models

# Create your models here.
    # --- Demographics ---
class User(AbstractUser):
    age = models.PositiveSmallIntegerField(null=True, blank=True)

    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOICES,
        null=True,
        blank=True
    )

    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)

    # --- Satisfaction ---
    satisfaction_score = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Score from 1 to 100"
    )

    # --- Metadata ---
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.username
    
class UserSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    session_start = models.DateTimeField()
    session_end = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    @property
    def duration_seconds(self):
        if self.session_end:
            return (self.session_end - self.session_start).total_seconds()
        return 0

    
class PageVisit(models.Model):
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    page = models.CharField(max_length=255)
    visited_at = models.DateTimeField(auto_now_add=True)
    time_spent_seconds = models.PositiveIntegerField(default=0)

# accounts/models.py
class DriverProfile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='driver_profile'
    )
    rating = models.FloatField(default=5.0)
    total_rides = models.PositiveIntegerField(default=0)
