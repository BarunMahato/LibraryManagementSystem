from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import User
from .permissions import IsLibrarian
from .serializers import UserSerializer


class MeAPIView(APIView):
    """Returns the currently authenticated user's profile, role, and live credits."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserListCreateAPIView(APIView):
    permission_classes = [IsLibrarian]

    def get(self, request):
        users = User.objects.all().order_by('-created_at')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        # Members can only view their own profile; Librarians can view anyone
        if request.user.role != User.Role.LIBRARIAN and not request.user.is_superuser and request.user.pk != pk:
            return Response(
                {"code": "FORBIDDEN", "message": "You can only view your own credit profile."},
                status=status.HTTP_403_FORBIDDEN,
            )
        user = get_object_or_404(User, pk=pk)
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)