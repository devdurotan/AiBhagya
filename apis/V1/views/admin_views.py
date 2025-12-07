from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from ..models import ReportsCategory, ReportMaster
from ..serializers.admin_serializers import ReportsCategorySerializer, ReportMasterSerializer


class IsAdminUser(permissions.BasePermission):
    """Custom permission to check if user is admin."""
    def has_permission(self, request, view):
        return request.user and request.user.is_staff


class ReportsCategoryViewSet(viewsets.ModelViewSet):
    """CRUD API for ReportsCategory with admin-only access. Supports file uploads."""
    queryset = ReportsCategory.objects.all()
    serializer_class = ReportsCategorySerializer
    # permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    parser_classes = (MultiPartParser, FormParser)
    filterset_fields = ['is_active', 'is_deleted']
    search_fields = ['category']
    ordering_fields = ['created_on', 'updated_on', 'category']

    def get_queryset(self):
        """Allow filtering by is_active and is_deleted."""
        queryset = ReportsCategory.objects.all()
        is_active = self.request.query_params.get('is_active')
        is_deleted = self.request.query_params.get('is_deleted')
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if is_deleted is not None:
            queryset = queryset.filter(is_deleted=is_deleted.lower() == 'true')
        
        return queryset.order_by('-created_on')


class ReportMasterViewSet(viewsets.ModelViewSet):
    """CRUD API for ReportMaster with admin-only access. Supports file uploads."""
    queryset = ReportMaster.objects.all()
    serializer_class = ReportMasterSerializer
    # permission_classes = [permissions.IsAuthenticated, IsAdminUser]
    parser_classes = (MultiPartParser, FormParser)
    filterset_fields = ['report_category', 'is_active', 'is_deleted']
    search_fields = ['title', 'description']
    ordering_fields = ['created_on', 'updated_on', 'title']

    def get_queryset(self):
        """Allow filtering by is_active, is_deleted, and report_category."""
        queryset = ReportMaster.objects.all()
        is_active = self.request.query_params.get('is_active')
        is_deleted = self.request.query_params.get('is_deleted')
        category_id = self.request.query_params.get('category')
        
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == 'true')
        if is_deleted is not None:
            queryset = queryset.filter(is_deleted=is_deleted.lower() == 'true')
        if category_id is not None:
            queryset = queryset.filter(report_category_id=category_id)
        
        return queryset.order_by('-created_on')
