from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.admin_views import AdViewSet, ReportsCategoryViewSet, ReportMasterViewSet, UserListViewSet

router = DefaultRouter()
router.register(r'report-categories', ReportsCategoryViewSet, basename='report-categories')
router.register(r'reports', ReportMasterViewSet, basename='reports')
router.register(r'users', UserListViewSet, basename='users')
router.register(r'ads', AdViewSet, basename='ads')


urlpatterns = [
    path('', include(router.urls)),
]
