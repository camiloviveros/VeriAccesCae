from django.db import models
from django.utils import timezone
from authentication.models import User

class AccessPoint(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    max_capacity = models.IntegerField(default=0)  # 0 significa sin límite
    current_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class AccessZone(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    access_points = models.ManyToManyField(AccessPoint, related_name='zones')
    max_capacity = models.IntegerField(default=0)
    current_count = models.IntegerField(default=0)
    
    def __str__(self):
        return self.name

class AccessCard(models.Model):
    card_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, related_name='access_cards', on_delete=models.CASCADE, null=True)
    is_active = models.BooleanField(default=True)
    issue_date = models.DateTimeField(auto_now_add=True)
    expiry_date = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Card {self.card_id} - {self.user.username if self.user else 'Unassigned'}"

class AccessPermission(models.Model):
    user = models.ForeignKey(User, related_name='access_permissions', on_delete=models.CASCADE)
    zone = models.ForeignKey(AccessZone, on_delete=models.CASCADE)
    time_from = models.TimeField(default='00:00:00')
    time_to = models.TimeField(default='23:59:59')
    valid_from = models.DateField(auto_now_add=True)
    valid_to = models.DateField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('user', 'zone')
    
    def __str__(self):
        return f"{self.user.username} - {self.zone.name}"

class AccessLog(models.Model):
    ACCESS_GRANTED = 'granted'
    ACCESS_DENIED = 'denied'
    ACCESS_STATUS = [
        (ACCESS_GRANTED, 'Access Granted'),
        (ACCESS_DENIED, 'Access Denied'),
    ]
    
    user = models.ForeignKey(User, related_name='access_logs', on_delete=models.CASCADE, null=True)
    access_point = models.ForeignKey(AccessPoint, on_delete=models.CASCADE)
    card_id = models.CharField(max_length=100, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=ACCESS_STATUS)
    reason = models.CharField(max_length=255, blank=True)
    direction = models.CharField(max_length=10, choices=[('in', 'Entry'), ('out', 'Exit')])
    
    def __str__(self):
        return f"{self.user.username if self.user else 'Unknown'} - {self.access_point.name} - {self.timestamp}"

class Visitor(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    id_number = models.CharField(max_length=50)
    phone = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    company = models.CharField(max_length=100, blank=True)
    photo = models.ImageField(upload_to='visitor_photos/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class VisitorAccess(models.Model):
    visitor = models.ForeignKey(Visitor, related_name='accesses', on_delete=models.CASCADE)
    host = models.ForeignKey(User, related_name='hosted_visitors', on_delete=models.CASCADE)
    purpose = models.CharField(max_length=255)
    valid_from = models.DateTimeField(auto_now_add=True)
    valid_to = models.DateTimeField()
    access_zones = models.ManyToManyField(AccessZone)
    qr_code = models.CharField(max_length=255, unique=True)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.visitor} - hosted by {self.host.username}"