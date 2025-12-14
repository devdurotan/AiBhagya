from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.app_views import CheckCart, RegistrationViewSet, ReportAdsAPIView, ReportsCategoryListViewSet, ReportMasterListViewSet, OtpVerifyViewSet,AddToCartApiViewSet,CartDetailsApiViewSet, UnwindFutureViewset, UserReportsApiViewSet

router = DefaultRouter()
router.register(r'register', RegistrationViewSet, basename='register')
router.register(r'otp-verify', OtpVerifyViewSet, basename='otp-verify')
router.register(r'report-categories', ReportsCategoryListViewSet, basename='report-categories')
router.register(r'reports', ReportMasterListViewSet, basename='reports')

# ------cart api
router.register('add_to_cart',AddToCartApiViewSet,basename='add_to_cart')
router.register('cart_details',CartDetailsApiViewSet,basename = 'cart_details')
router.register('cart_toggle',CheckCart,basename='cart_toggle')
router.register('unwind_future',UnwindFutureViewset,basename='unwind_future')
router.register('user_reports',UserReportsApiViewSet,basename='user_reports')


urlpatterns = [
    path('', include(router.urls)),
    path('reports/<int:report_id>/ads/',ReportAdsAPIView.as_view(),name='report-ads')

]
