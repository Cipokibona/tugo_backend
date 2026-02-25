from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Notification
        fields = [
            'id',
            'recipient',
            'sender',
            'sender_username',
            'title',
            'message',
            'notification_type',
            'is_read',
            'created_at',
        ]
        read_only_fields = ['sender', 'sender_username', 'created_at']
