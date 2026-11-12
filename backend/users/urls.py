from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import MeAPIView, SignupAPIView, UserDetailAPIView, UserListCreateAPIView

urlpatterns = [
    # JWT Auth Endpoints
    path('auth/login/', TokenObtainPairView.as_view(), name='token-obtain-pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/me/', MeAPIView.as_view(), name='auth-me'),
    path('auth/signup/', SignupAPIView.as_view(), name='auth-signup'),

    # Member & Credit Profile Endpoints
    path('users/', UserListCreateAPIView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserDetailAPIView.as_view(), name='user-detail'),
]
