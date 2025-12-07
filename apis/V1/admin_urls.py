from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.admin_views import ReportsCategoryViewSet, ReportMasterViewSet

router = DefaultRouter()
router.register(r'report-categories', ReportsCategoryViewSet, basename='report-categories')
router.register(r'reports', ReportMasterViewSet, basename='reports')

urlpatterns = [
    path('', include(router.urls)),
]
