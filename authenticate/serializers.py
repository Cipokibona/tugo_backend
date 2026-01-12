from rest_framework import serializers
from .models import User, DriverProfile

class DriverProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = DriverProfile
        fields = ['rating', 'total_rides']

class UserSerializer(serializers.ModelSerializer):
    driver_profile = DriverProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'age',
            'gender',
            'city',
            'country',
            'satisfaction_score',
            'driver_profile',
            'created_at',
            'updated_at',
        ]
