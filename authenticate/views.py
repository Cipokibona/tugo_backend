from django.shortcuts import render
from rest_framework import viewsets, permissions
from .models import User, DriverProfile
from .serializers import UserSerializer, DriverProfileSerializer

# API pour les utilisateurs
class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]  # seulement les users authentifiés

# API pour les profils conducteur
class DriverProfileViewSet(viewsets.ModelViewSet):
    queryset = DriverProfile.objects.all()
    serializer_class = DriverProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

