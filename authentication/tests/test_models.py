from django.test import TestCase
from django.contrib.auth import get_user_model
from authentication.models import Role, Permission, UserProfile

User = get_user_model()

class UserModelTest(TestCase):
    def setUp(self):
        self.role = Role.objects.create(name="User", description="Basic user role")
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword123"
        )
        self.profile = UserProfile.objects.create(user=self.user, role=self.role)
    
    def test_user_creation(self):
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.email, "test@example.com")
        self.assertTrue(self.user.check_password("testpassword123"))
        self.assertEqual(self.user.login_attempts, 0)
        self.assertFalse(self.user.is_locked)
    
    def test_user_profile_association(self):
        self.assertEqual(self.user.profile, self.profile)
        self.assertEqual(self.profile.role, self.role)