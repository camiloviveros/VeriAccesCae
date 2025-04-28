from django.test import TestCase
from django.contrib.auth import get_user_model
from security.models import (
    SecurityIncident, EmergencyProtocol, 
    SecurityCheckpoint, SecurityRound, SecurityRoundExecution
)
from access_control.models import AccessPoint
from django.utils import timezone

User = get_user_model()

class SecurityIncidentTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='securityuser',
            email='security@example.com',
            password='password123'
        )
        
        self.incident = SecurityIncident.objects.create(
            title='Unauthorized access attempt',
            description='Someone tried to access the server room without permission',
            location='Server Room',
            severity=SecurityIncident.MEDIUM,
            reported_by=self.user,
            status='new'
        )
    
    def test_incident_creation(self):
        self.assertEqual(self.incident.title, 'Unauthorized access attempt')
        self.assertEqual(self.incident.severity, SecurityIncident.MEDIUM)
        self.assertEqual(self.incident.status, 'new')
        self.assertEqual(self.incident.reported_by, self.user)

class EmergencyProtocolTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='securityadmin',
            email='secadmin@example.com',
            password='password123'
        )
        
        self.protocol = EmergencyProtocol.objects.create(
            name='Fire Evacuation',
            description='Protocol for building evacuation in case of fire',
            instructions='1. Activate alarms\n2. Call fire department\n3. Evacuate building',
            created_by=self.user
        )
    
    def test_protocol_creation(self):
        self.assertEqual(self.protocol.name, 'Fire Evacuation')
        self.assertTrue('evacuate building' in self.protocol.instructions.lower())
        self.assertEqual(self.protocol.created_by, self.user)