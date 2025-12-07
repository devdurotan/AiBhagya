from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.app_views import RegistrationViewSet, ReportsCategoryListViewSet, ReportMasterListViewSet, OtpVerifyViewSet

router = DefaultRouter()
router.register(r'register', RegistrationViewSet, basename='register')
router.register(r'otp-verify', OtpVerifyViewSet, basename='otp-verify')
router.register(r'report-categories', ReportsCategoryListViewSet, basename='report-categories')
router.register(r'reports', ReportMasterListViewSet, basename='reports')

urlpatterns = [
    path('', include(router.urls)),
]
