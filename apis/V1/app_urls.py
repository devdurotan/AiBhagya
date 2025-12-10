from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.app_views import RegistrationViewSet, ReportsCategoryListViewSet, ReportMasterListViewSet, OtpVerifyViewSet,AddToCartApiViewSet,CartDetailsApiViewSet

router = DefaultRouter()
router.register(r'register', RegistrationViewSet, basename='register')
router.register(r'otp-verify', OtpVerifyViewSet, basename='otp-verify')
router.register(r'report-categories', ReportsCategoryListViewSet, basename='report-categories')
router.register(r'reports', ReportMasterListViewSet, basename='reports')

# ------cart api
router.register('add_to_cart',AddToCartApiViewSet,basename='add_to_cart')
router.register('cart_details',CartDetailsApiViewSet,basename = 'cart_details')

urlpatterns = [
    path('', include(router.urls)),
]
