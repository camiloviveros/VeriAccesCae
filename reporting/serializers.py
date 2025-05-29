
from rest_framework import serializers
from .models import Report, GeneratedReport, ReportSchedule
from authentication.models import User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']

class ReportSerializer(serializers.ModelSerializer):
    created_by_detail = UserSerializer(source='created_by', read_only=True)
    
    class Meta:
        model = Report
        fields = ['id', 'name', 'description', 'report_type', 'period', 
                  'filters', 'created_by', 'created_by_detail', 'created_at']
        read_only_fields = ['created_at']

class GeneratedReportSerializer(serializers.ModelSerializer):
    report_detail = ReportSerializer(source='report', read_only=True)
    generated_by_detail = UserSerializer(source='generated_by', read_only=True)
    
    class Meta:
        model = GeneratedReport
        fields = ['id', 'report', 'report_detail', 'file', 'format', 
                  'period_start', 'period_end', 'generated_at', 
                  'generated_by', 'generated_by_detail']
        read_only_fields = ['generated_at']

class ReportScheduleSerializer(serializers.ModelSerializer):
    report_detail = ReportSerializer(source='report', read_only=True)
    
    class Meta:
        model = ReportSchedule
        fields = '__all__'