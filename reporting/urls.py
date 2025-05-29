# reporting/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReportViewSet, GeneratedReportViewSet, ReportScheduleViewSet

# Router
router = DefaultRouter()
router.register(r'definitions', ReportViewSet)
router.register(r'generated', GeneratedReportViewSet)
router.register(r'schedules', ReportScheduleViewSet)

urlpatterns = [
    path('', include(router.urls)),
]