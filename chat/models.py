from django.db import models
from ride.models import Ride
from django.conf import settings

User = settings.AUTH_USER_MODEL
# Create your models here.
class Conversation(models.Model):
    ride = models.OneToOneField(
        Ride,
        on_delete=models.CASCADE,
        related_name='conversation'
    )

    participants = models.ManyToManyField(User)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Chat for ride {self.ride.id}"
    
class Message(models.Model):

    MESSAGE_TYPES = (
        ('TEXT', 'Text'),
        ('AUDIO', 'Audio'),
        ('IMAGE', 'Image'),
        ('FILE', 'File'),
        ('CALL', 'Call'),  # logs appels
    )

    conversation = models.ForeignKey(
        'Conversation',
        on_delete=models.CASCADE,
        related_name='messages'
    )

    sender = models.ForeignKey(User, on_delete=models.CASCADE)

    message_type = models.CharField(
        max_length=10,
        choices=MESSAGE_TYPES,
        default='TEXT'
    )

    # Contenu
    content = models.TextField(null=True, blank=True)
    media_file = models.FileField(
        upload_to='chat_media/',
        null=True,
        blank=True
    )

    media_duration = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Audio/video duration in seconds"
    )

    # Meta
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.message_type} - {self.sender}"
