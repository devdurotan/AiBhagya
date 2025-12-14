from apis.V1.views.app_views import create_response
from rest_framework import viewsets, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser

from ..models import ReportsCategory, ReportMaster, UserMaster
from ..serializers.admin_serializers import ReportsCategorySerializer, ReportMasterSerializer, UserMasterSerializer


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
    


class UserListViewSet(viewsets.ReadOnlyModelViewSet):
    """GET-only API for User Master. Requires authentication."""
    queryset = UserMaster.objects.filter(is_active=True, is_deleted=False)
    serializer_class = UserMasterSerializer
    # permission_classes = [permissions.IsAuthenticated]
    search_fields = ['first_name', 'last_name', 'email', 'full_name']
    ordering_fields = ['id']

    def get_queryset(self):
        """Filter users by category_id if provided, otherwise return all active users."""
        queryset = UserMaster.objects.filter(is_active=True, is_deleted=False)
        category_id = self.request.query_params.get('category_id')
        
        if category_id:
            queryset = queryset.filter(report_category_id=category_id)
        
        return queryset.order_by('-id')

    def list(self, request, *args, **kwargs):
        """Override list to return custom response format."""
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return create_response(True, 'Data fetched successfully', serializer.data)

    def retrieve(self, request, *args, **kwargs):
        """Override retrieve to return custom response format."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return create_response(True, 'Data fetched successfully', serializer.data)

