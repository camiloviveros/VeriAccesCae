from django.test import TestCase
from django.contrib.auth import get_user_model
from access_control.models import AccessPoint, AccessZone, AccessCard, AccessLog
from datetime import datetime

User = get_user_model()

class AccessControlModelsTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="securityuser",
            email="security@example.com",
            password="password123"
        )
        self.access_point = AccessPoint.objects.create(
            name="Main Entrance",
            location="Building A",
            max_capacity=100
        )
        self.access_zone = AccessZone.objects.create(
            name="Office Area",
            max_capacity=50
        )
        self.access_zone.access_points.add(self.access_point)
        
    def test_access_point_creation(self):
        self.assertEqual(self.access_point.name, "Main Entrance")
        self.assertEqual(self.access_point.current_count, 0)
        
    def test_access_zone_association(self):
        self.assertIn(self.access_point, self.access_zone.access_points.all())
        
    def test_access_log_creation(self):
        log = AccessLog.objects.create(
            user=self.user,
            access_point=self.access_point,
            status=AccessLog.ACCESS_GRANTED,
            direction="in"
        )
        self.assertEqual(log.user, self.user)
        self.assertEqual(log.access_point, self.access_point)
        self.assertEqual(log.status, AccessLog.ACCESS_GRANTED)