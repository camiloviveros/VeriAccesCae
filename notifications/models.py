from django.db import models
from authentication.models import User

class NotificationTemplate(models.Model):
    code = models.CharField(max_length=100, unique=True)
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=200)
    content = models.TextField()
    
    def __str__(self):
        return self.name

class Notification(models.Model):
    EMAIL = 'email'
    PUSH = 'push'
    SMS = 'sms'
    IN_APP = 'in_app'
    
    TYPE_CHOICES = [
        (EMAIL, 'Email'),
        (PUSH, 'Push Notification'),
        (SMS, 'SMS'),
        (IN_APP, 'In-App Notification'),
    ]
    
    recipient = models.ForeignKey(User, related_name='notifications', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=10, choices=TYPE_CHOICES)
    read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.notification_type} to {self.recipient.username} - {self.created_at}"

class NotificationPreference(models.Model):
    user = models.OneToOneField(User, related_name='notification_preferences', on_delete=models.CASCADE)
    email_enabled = models.BooleanField(default=True)
    push_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=False)
    in_app_enabled = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Notification preferences for {self.user.username}"