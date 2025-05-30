
from rest_framework import serializers
from .models import (
    SecurityIncident, IncidentAttachment, IncidentComment,
    EmergencyProtocol, EmergencyEvent,
    SecurityCheckpoint, SecurityRound, SecurityRoundCheckpoint,
    SecurityRoundExecution, CheckpointScan
)
from authentication.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class SecurityIncidentSerializer(serializers.ModelSerializer):
    reported_by_detail = UserSerializer(source='reported_by', read_only=True)
    assigned_to_detail = UserSerializer(source='assigned_to', read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = SecurityIncident
        fields = ['id', 'title', 'description', 'location', 'severity', 'severity_display',
                  'reported_by', 'reported_by_detail', 'assigned_to', 
                  'assigned_to_detail', 'status', 'status_display', 
                  'report_type', 'report_type_display',
                  'created_at', 'updated_at', 'resolved_at']
        read_only_fields = ['created_at', 'updated_at']

class IncidentCommentSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = IncidentComment
        fields = ['id', 'incident', 'user', 'user_detail', 'comment', 
                  'created_at', 'is_system_comment']
        read_only_fields = ['created_at']

class EmergencyProtocolSerializer(serializers.ModelSerializer):
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = EmergencyProtocol
        fields = ['id', 'name', 'description', 'instructions', 'is_active',
                  'created_by', 'created_by_detail', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']

class EmergencyEventSerializer(serializers.ModelSerializer):
    protocol_detail = EmergencyProtocolSerializer(source='protocol', read_only=True)
    activated_by_detail = UserSerializer(source='activated_by', read_only=True)
    
    class Meta:
        model = EmergencyEvent
        fields = '__all__'

class SecurityCheckpointSerializer(serializers.ModelSerializer):
    class Meta:
        model = SecurityCheckpoint
        fields = '__all__'

class SecurityRoundSerializer(serializers.ModelSerializer):
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    checkpoints_count = serializers.SerializerMethodField()
    
    class Meta:
        model = SecurityRound
        fields = ['id', 'name', 'description', 'created_by', 'created_by_detail',
                  'created_at', 'is_active', 'estimated_duration', 'checkpoints_count']
        read_only_fields = ['created_at']
    
    def get_checkpoints_count(self, obj):
        return obj.checkpoints.count()

class SecurityRoundExecutionSerializer(serializers.ModelSerializer):
    round_detail = SecurityRoundSerializer(source='round', read_only=True)
    guard_detail = UserSerializer(source='guard', read_only=True)
    progress = serializers.SerializerMethodField()
    
    class Meta:
        model = SecurityRoundExecution
        fields = ['id', 'round', 'round_detail', 'guard', 'guard_detail',
                  'start_time', 'end_time', 'status', 'notes', 'progress']
        read_only_fields = ['start_time']
    
    def get_progress(self, obj):
        total_checkpoints = obj.round.checkpoints.count()
        scanned_checkpoints = obj.scans.count()
        return {
            'total': total_checkpoints,
            'scanned': scanned_checkpoints,
            'percentage': (scanned_checkpoints / total_checkpoints * 100) if total_checkpoints > 0 else 0
        }