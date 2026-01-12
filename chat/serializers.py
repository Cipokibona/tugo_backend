from rest_framework import serializers
from django.conf import settings
from .models import Conversation, Message
from ride.serializers import RideSerializer

User = settings.AUTH_USER_MODEL

class MessageSerializer(serializers.ModelSerializer):
    sender_username = serializers.CharField(source='sender.username', read_only=True)

    class Meta:
        model = Message
        fields = [
            'id',
            'conversation',
            'sender',
            'sender_username',
            'message_type',
            'content',
            'media_file',
            'media_duration',
            'is_read',
            'created_at',
        ]


class ConversationSerializer(serializers.ModelSerializer):
    ride_details = RideSerializer(source='ride', read_only=True)
    messages = MessageSerializer(many=True, read_only=True)
    participants_usernames = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            'id',
            'ride',
            'ride_details',
            'participants',
            'participants_usernames',
            'created_at',
            'messages',
        ]

    def get_participants_usernames(self, obj):
        return [user.username for user in obj.participants.all()]
