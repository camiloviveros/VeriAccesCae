from django.db import models
from authentication.models import User

class Report(models.Model):
    DAILY = 'daily'
    WEEKLY = 'weekly'
    MONTHLY = 'monthly'
    CUSTOM = 'custom'
    
    PERIOD_CHOICES = [
        (DAILY, 'Daily'),
        (WEEKLY, 'Weekly'),
        (MONTHLY, 'Monthly'),
        (CUSTOM, 'Custom'),
    ]
    
    ACCESS_LOGS = 'access_logs'
    INCIDENTS = 'incidents'
    ATTENDANCE = 'attendance'
    PARKING = 'parking'
    VISITORS = 'visitors'
    
    TYPE_CHOICES = [
        (ACCESS_LOGS, 'Access Logs'),
        (INCIDENTS, 'Security Incidents'),
        (ATTENDANCE, 'Attendance'),
        (PARKING, 'Parking Usage'),
        (VISITORS, 'Visitor Statistics'),
    ]
    
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    report_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    period = models.CharField(max_length=10, choices=PERIOD_CHOICES)
    filters = models.JSONField(default=dict)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.report_type}"

class GeneratedReport(models.Model):
    report = models.ForeignKey(Report, related_name='generated_reports', on_delete=models.CASCADE)
    file = models.FileField(upload_to='reports/')
    format = models.CharField(max_length=10, choices=[('pdf', 'PDF'), ('xlsx', 'Excel'), ('csv', 'CSV')])
    period_start = models.DateField()
    period_end = models.DateField()
    generated_at = models.DateTimeField(auto_now_add=True)
    generated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"{self.report.name} - {self.period_start} to {self.period_end}"

class ReportSchedule(models.Model):
    report = models.ForeignKey(Report, related_name='schedules', on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    recipients = models.ManyToManyField(User, related_name='report_subscriptions')
    
    # Campos para programación
    run_daily = models.BooleanField(default=False)
    run_weekly = models.BooleanField(default=False)
    day_of_week = models.IntegerField(null=True, blank=True, help_text="0=Monday, 6=Sunday")
    run_monthly = models.BooleanField(default=False)
    day_of_month = models.IntegerField(null=True, blank=True)
    run_time = models.TimeField(help_text="Hora de ejecución en UTC")
    
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        schedule_type = "daily" if self.run_daily else "weekly" if self.run_weekly else "monthly" if self.run_monthly else "custom"
        return f"{self.report.name} - {schedule_type}"