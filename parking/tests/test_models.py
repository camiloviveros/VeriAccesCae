from django.test import TestCase
from django.contrib.auth import get_user_model
from parking.models import ParkingArea, Vehicle, ParkingAccess, ParkingLog

User = get_user_model()

class ParkingAreaTest(TestCase):
    def setUp(self):
        self.parking_area = ParkingArea.objects.create(
            name='Main Parking',
            description='Main building parking area',
            max_capacity=50,
            current_count=0,
            is_active=True
        )
    
    def test_parking_area_creation(self):
        self.assertEqual(self.parking_area.name, 'Main Parking')
        self.assertEqual(self.parking_area.max_capacity, 50)
        self.assertEqual(self.parking_area.current_count, 0)
        self.assertTrue(self.parking_area.is_active)

class VehicleTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='carowner',
            email='owner@example.com',
            password='password123'
        )
        
        self.vehicle = Vehicle.objects.create(
            user=self.user,
            license_plate='ABC123',
            brand='Toyota',
            model='Corolla',
            color='Blue',
            is_active=True
        )
    
    def test_vehicle_creation(self):
        self.assertEqual(self.vehicle.license_plate, 'ABC123')
        self.assertEqual(self.vehicle.brand, 'Toyota')
        self.assertEqual(self.vehicle.model, 'Corolla')
        self.assertEqual(self.vehicle.user, self.user)
        self.assertTrue(self.vehicle.is_active)