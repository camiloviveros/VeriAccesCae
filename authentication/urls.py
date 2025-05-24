from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    LogoutView,
    ChangePasswordView,
    UserViewSet,
    CurrentUserView,
    RoleViewSet,
    PermissionViewSet,
    RegisterView
)


router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'roles', RoleViewSet)
router.register(r'permissions', PermissionViewSet)

urlpatterns = [
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
     path('register/', RegisterView.as_view(), name='register'),
    
    path('me/', CurrentUserView.as_view(), name='current_user'),
    

    path('', include(router.urls)),
]