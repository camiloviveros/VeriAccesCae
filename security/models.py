from django.db import models
from django.utils import timezone
from authentication.models import User
from access_control.models import AccessPoint, AccessZone

class SecurityIncident(models.Model):
    CRITICAL = 'critical'
    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    
    SEVERITY_CHOICES = [
        (CRITICAL, 'Critical'),
        (HIGH, 'High'),
        (MEDIUM, 'Medium'),
        (LOW, 'Low'),
    ]
    
    STATUS_CHOICES = [
        ('new', 'New'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=200)
    severity = models.CharField(max_length=10, choices=SEVERITY_CHOICES, default=MEDIUM)
    reported_by = models.ForeignKey(User, related_name='reported_incidents', on_delete=models.CASCADE)
    assigned_to = models.ForeignKey(User, related_name='assigned_incidents', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return self.title
    
    def resolve(self, resolved_by):
        """
        Marca el incidente como resuelto.
        """
        self.status = 'resolved'
        self.resolved_at = timezone.now()
        self.save()
        
        # Registrar la resolución
        IncidentComment.objects.create(
            incident=self,
            user=resolved_by,
            comment=f"Incidente marcado como resuelto por {resolved_by.get_full_name() or resolved_by.username}",
            is_system_comment=True
        )

class IncidentAttachment(models.Model):
    """
    Archivos adjuntos a incidentes de seguridad.
    """
    incident = models.ForeignKey(SecurityIncident, related_name='attachments', on_delete=models.CASCADE)
    file = models.FileField(upload_to='incident_attachments/')
    description = models.CharField(max_length=200, blank=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Attachment for {self.incident.title}"

class IncidentComment(models.Model):
    """
    Comentarios sobre incidentes de seguridad.
    """
    incident = models.ForeignKey(SecurityIncident, related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_system_comment = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.incident.title}"

class EmergencyProtocol(models.Model):
    """
    Protocolos para situaciones de emergencia.
    """
    name = models.CharField(max_length=100)
    description = models.TextField()
    instructions = models.TextField()
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name

class EmergencyEvent(models.Model):
    """
    Registro de activaciones de protocolos de emergencia.
    """
    protocol = models.ForeignKey(EmergencyProtocol, on_delete=models.CASCADE)
    activated_by = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    affected_zones = models.ManyToManyField(AccessZone, blank=True)
    
    def __str__(self):
        return f"{self.protocol.name} - {self.timestamp}"
    
    def end_emergency(self, user, notes=""):
        """
        Finaliza la situación de emergencia.
        """
        self.ended_at = timezone.now()
        self.notes = notes
        self.save()

class SecurityCheckpoint(models.Model):
    """
    Puntos de control para rondas de vigilancia.
    """
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    access_point = models.ForeignKey(AccessPoint, on_delete=models.SET_NULL, null=True, blank=True)
    qr_code = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name

class SecurityRound(models.Model):
    """
    Rondas de vigilancia programadas.
    """
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    estimated_duration = models.IntegerField(help_text="Duración estimada en minutos", default=30)
    
    def __str__(self):
        return self.name

class SecurityRoundCheckpoint(models.Model):
    """
    Relación entre rondas y puntos de control, con orden específico.
    """
    round = models.ForeignKey(SecurityRound, related_name="checkpoints", on_delete=models.CASCADE)
    checkpoint = models.ForeignKey(SecurityCheckpoint, on_delete=models.CASCADE)
    order = models.IntegerField()
    estimated_time = models.IntegerField(help_text="Tiempo estimado en minutos desde el punto anterior", default=5)
    
    class Meta:
        unique_together = ('round', 'checkpoint', 'order')
        ordering = ['order']
    
    def __str__(self):
        return f"{self.round.name} - {self.checkpoint.name} - {self.order}"

class SecurityRoundExecution(models.Model):
    """
    Ejecución de una ronda de vigilancia.
    """
    STATUSES = [
        ('in_progress', 'En Progreso'),
        ('completed', 'Completada'),
        ('incomplete', 'Incompleta'),
        ('late', 'Tarde'),
        ('canceled', 'Cancelada')
    ]
    
    round = models.ForeignKey(SecurityRound, on_delete=models.CASCADE)
    guard = models.ForeignKey(User, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUSES, default='in_progress')
    notes = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.round.name} - {self.guard.username} - {self.start_time}"
    
    def complete(self):
        """
        Marca la ronda como completada.
        """
        if self.status == 'in_progress':
            all_checkpoints = self.round.checkpoints.count()
            scanned_checkpoints = self.scans.count()
            
            if all_checkpoints == scanned_checkpoints:
                self.status = 'completed'
            else:
                self.status = 'incomplete'
                
            self.end_time = timezone.now()
            self.save()
    
    def cancel(self, reason):
        """
        Cancela la ejecución de la ronda.
        """
        self.status = 'canceled'
        self.notes = reason
        self.end_time = timezone.now()
        self.save()

class CheckpointScan(models.Model):
    """
    Registro de escaneo de punto de control durante una ronda.
    """
    execution = models.ForeignKey(SecurityRoundExecution, related_name='scans', on_delete=models.CASCADE)
    checkpoint = models.ForeignKey(SecurityCheckpoint, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('execution', 'checkpoint')
    
    def __str__(self):
        return f"{self.execution.round.name} - {self.checkpoint.name} - {self.timestamp}"