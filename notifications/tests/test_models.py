from django.test import TestCase
from django.contrib.auth import get_user_model
from notifications.models import NotificationTemplate, Notification

User = get_user_model()

class NotificationTemplateTest(TestCase):
    def setUp(self):
        self.template = NotificationTemplate.objects.create(
            code='access_denied',
            name='Access Denied Template',
            subject='Access Denied Alert',
            content='Your access attempt to {location} at {time} was denied. Reason: {reason}'
        )
    
    def test_template_creation(self):
        self.assertEqual(self.template.code, 'access_denied')
        self.assertEqual(self.template.name, 'Access Denied Template')
        self.assertIn('{location}', self.template.content)
        self.assertIn('{time}', self.template.content)

class NotificationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='notifyuser',
            email='notify@example.com',
            password='password123'
        )
        
        self.notification = Notification.objects.create(
            recipient=self.user,
            title='Security Alert',
            message='Unauthorized access attempt detected',
            notification_type=Notification.IN_APP,
            read=False
        )
    
    def test_notification_creation(self):
        self.assertEqual(self.notification.recipient, self.user)
        self.assertEqual(self.notification.title, 'Security Alert')
        self.assertEqual(self.notification.notification_type, Notification.IN_APP)
        self.assertFalse(self.notification.read)