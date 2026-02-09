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

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['first_name', 'contact_number', 'username', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(
            first_name=validated_data['first_name'],
            contact_number=validated_data.get('contact_number'),
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user
