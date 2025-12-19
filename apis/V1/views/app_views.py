import random
from datetime import timedelta

from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken

from AiBhagya.settings import BASE_URL
from apis.V1.utils.app_utils import get_ads_for_report
from ..serializers.otp_serializers import OtpVerifySerializer

from ..models import Ad, AdWatch, Cart, UserGeneratedReport, UserMaster, OtpCode, ReportsCategory, ReportMaster
from ..serializers.app_serializers import AddToCartSerializer, CheckCartSerializer, GlobalSerializer, UserRegistrationSerializer
from ..serializers.admin_serializers import AdSerializer, AdWatchUpdateSerializer, ReportsCategorySerializer, ReportMasterSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404 


from django.db import transaction
import pandas as pd
import datetime
def _generate_otp(n=6):
    return ''.join(str(random.randint(0, 9)) for _ in range(n))


from rest_framework import mixins, viewsets
class OtpVerifyViewSet(viewsets.GenericViewSet, mixins.CreateModelMixin):
    """Verify OTP and return JWT tokens."""
    serializer_class = OtpVerifySerializer
    http_method_names = ['post']

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        code = serializer.validated_data['code']

        # Find OTP
        otp_obj = OtpCode.objects.filter(email__iexact=email, code=code, is_used=False, expires_on__gte=timezone.now()).first()
        if not otp_obj:
            return Response({
                'status': False,
                'message': 'Invalid or expired OTP.',
                'data': None
            }, status=status.HTTP_400_BAD_REQUEST)

        # Mark OTP as used
        otp_obj.is_used = True
        otp_obj.save()

        # Get or create user
        user = UserMaster.objects.filter(email__iexact=email).first()
        if not user:
            return Response({
                'status': False,
                'message': 'User not found for this email.',
                'data': None
            }, status=status.HTTP_404_NOT_FOUND)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }
        return Response({
            'status': True,
            'message': 'OTP verified. Login successful.',
            'data': data
        }, status=status.HTTP_200_OK)


class RegistrationViewSet(viewsets.ModelViewSet):
    """Handle user registration via POST. If email exists, send OTP; otherwise create user and send OTP."""
    serializer_class = UserRegistrationSerializer
    queryset = UserMaster.objects.all()
    http_method_names = ['post']

    def _send_otp_email(self, email, code, user=None):
        context = {
            'code': code,
            'user': user,
            'expiry_minutes': 10,
        }
        subject = 'Your verification code'
        text_content = render_to_string('email/registration_otp.txt', context)
        html_content = render_to_string('email/registration_otp.html', context)
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', None)
        message = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=from_email,
            to=[email],
        )
        message.attach_alternative(html_content, "text/html")
        print(message," sent to ", email)
        message.send(fail_silently=False)

    def create(self, request, *args, **kwargs):
        email = request.data.get('email')
        if not email:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        existing = UserMaster.objects.filter(email__iexact=email).first()

        # generate otp and store
        code = _generate_otp()
        expires_on = timezone.now() + timedelta(minutes=10)
        OtpCode.objects.create(email=email, code=code, expires_on=expires_on)

        if existing:
            # send otp to existing user
            self._send_otp_email(email, code, user=existing)
            return Response({'detail': 'User exists. OTP sent to email.'}, status=status.HTTP_200_OK)

        # create user
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # send otp to newly created user
        self._send_otp_email(email, code, user=user)

        return Response({'detail': 'User created. OTP sent to email.'}, status=status.HTTP_201_CREATED)


def create_response(status_code, message, data=None):
    """Create standardized API response format."""
    return Response({
        'status': status_code,
        'message': message,
        'data': data or {}
    })


class ReportsCategoryListViewSet(viewsets.ReadOnlyModelViewSet):
    """GET-only API for ReportsCategory. Requires authentication."""
    queryset = ReportsCategory.objects.filter(is_active=True, is_deleted=False)
    serializer_class = ReportsCategorySerializer
    # permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['is_active']
    search_fields = ['category']
    ordering_fields = ['created_on', 'category']

    def get_queryset(self):
        """Return only active, non-deleted categories."""
        return ReportsCategory.objects.filter(is_active=True, is_deleted=False).order_by('category')

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


class ReportMasterListViewSet(viewsets.ReadOnlyModelViewSet):
    """GET-only API for ReportMaster. Requires authentication."""
    queryset = ReportMaster.objects.filter(is_active=True, is_deleted=False)
    serializer_class = ReportMasterSerializer
    # permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ['report_category']
    search_fields = ['title', 'description']
    ordering_fields = ['created_on', 'title']

    def get_queryset(self):
        """Filter reports by category_id if provided, otherwise return all active reports."""
        queryset = ReportMaster.objects.filter(is_active=True, is_deleted=False)
        category_id = self.request.query_params.get('category_id')
        
        if category_id:
            queryset = queryset.filter(report_category_id=category_id)
        
        return queryset.order_by('-created_on')

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



# --------------add to cart api view set---
class AddToCartApiViewSet(viewsets.GenericViewSet):
    serializer_class = AddToCartSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        payload = request.data

        # single → list
        if isinstance(payload, dict):
            payload = [payload]

        if not isinstance(payload, list):
            return Response(
                {"detail": "Invalid payload format"},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = self.get_serializer(data=payload, many=True)
        serializer.is_valid(raise_exception=True)

        items = serializer.validated_data
        user = request.user

        for item in items:
            report_id = item['report_id']
            rep = ReportMaster.objects.filter(id=item['report_id']).last()

            cart_obj, created = Cart.objects.get_or_create(
                user=user,
                report_id=report_id,
                amount= rep.price
            )

            # agar pehle se cart me hai → quantity add
            if not created:
                cart_obj.save()

        return Response(
            {   "status": True,
                "message": "Reports added to cart successfully"
            },
            status=status.HTTP_201_CREATED
        )



# cart details viewSet
class CartDetailsApiViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]

    def list(self, request, *args, **kwargs):
        user = request.user
        print(user)

        # Query raw cart items
        carts = Cart.objects.filter(user=user).select_related(
            "report",
            "report__report_category"
        )

        # Convert queryset → list of dictionaries
        raw_data = [
            {
                "id": c.id,
                "title": c.report.title,
                "short_description": c.report.report_category.short_desc,
                "quantity": c.quantity,
                "amount": c.amount,     
                "is_checked": c.is_checked,     
            }
            for c in carts
        ]

        # Create DataFrame
        df = pd.DataFrame(raw_data)

        if df.empty:
            return Response({
                "status": True,
                "message": "Cart is empty.",
                "data": []
            })

        # Convert df → list of dictionaries
        final_output = df.to_dict(orient="records")

        return Response({
            "status": True,
            "message": "Cart details fetched successfully.",
            "data": final_output
        })
    


class CheckCart(viewsets.GenericViewSet):
    serializer_class = CheckCartSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        user = request.user
        cart_id = request.data.get('cart_id')
        cart = Cart.objects.filter(id=cart_id, user=user).last()
        if not cart:
            return Response(
                {   "status": False,
                    "message": "Cart not found"
                },
                status=status.HTTP_404_NOT_FOUND
            )
        if cart.is_checked:
            cart.is_checked = False
            message = "Report unselected."
        else:
            cart.is_checked = True
            message = "Report selected."
        cart.save()

        return Response(
            {   "status": True,
                "message": message
            },
            status=status.HTTP_201_CREATED
        )



class UnwindFutureViewset(viewsets.GenericViewSet):
    serializer_class = GlobalSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        user = request.user
        cart = Cart.objects.filter(user=user, is_checked=True).all()
        if not cart:
            return Response(
            {   "status": True,
                "message": "Report not found."
            },
            status=status.HTTP_200_OK
        )

        for item in cart:
            user_report = UserGeneratedReport()
            user_report.user = user
            user_report.report = item.report
            user_report.report_category = item.report.report_category
            user_report.amount = item.report.price
            user_report.credit = item.report.price
            user_report.save()

        cart.delete()
        

        return Response(
            {   "status": True,
                "message": "Reports generated successfully"
            },
            status=status.HTTP_201_CREATED
        )
    


class UserReportsApiViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]

    def list(self, request, *args, **kwargs):
        user = request.user
        print(user)

        # Query raw cart items
        user_reports = UserGeneratedReport.objects.filter(user=user).select_related(
            "report",
            "report__report_category",
            "user",


        )

        # Convert queryset → list of dictionaries
        raw_data = [
            {
                "id": report.id,
                "title": f"{request.user.full_name}_{report.report.title}_{datetime.datetime.now()}",
                "amount": report.amount, 
                "image": f"{BASE_URL}{report.report.file.url}",
                "is_locked":report.is_locked,
                "report_id":report.report.id

            }
            for report in user_reports
        ]

        # Create DataFrame
        df = pd.DataFrame(raw_data)

        if df.empty:
            return Response({
                "status": True,
                "message": "Section is empty.",
                "data": []
            })

        # Convert df → list of dictionaries
        final_output = df.to_dict(orient="records")

        return Response({
            "status": True,
            "message": "Data fetched successfully.",
            "data": final_output
        })
    


class ReportAdsAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, report_id):
        report = get_object_or_404(ReportMaster, id=report_id)

        # already unlocked?
        unlocked = UserGeneratedReport.objects.filter(
            user=request.user,
            report=report,
            is_locked=False
        ).exists()

        if unlocked:
            return Response({
                "locked": False,
                "message": "Report already unlocked"
            })

        ads = get_ads_for_report(request.user, report)

        if not ads:
            return Response({
                "locked": True,
                "message": "No ads available right now"
            })

        return Response({
            "locked": True,
            "ads_required": settings.ADS_REQUIRED_PER_REPORT,
            "ads": AdSerializer(ads, many=True).data
        })

from django.db.models import Sum

class AdWatchCompleteAPIView(APIView):
    
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AdWatchUpdateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
        report = get_object_or_404(ReportMaster, id=serializer.validated_data['report_id'])
        ad = get_object_or_404(Ad, id=serializer.validated_data['ad_id'], is_active=True)

        # ✅ Track ad for this report + user
        ad_watch, created = AdWatch.objects.get_or_create(
            user=user,
            report=report,
            ad=ad
        )

        # Mark ad completed
        ad_watch.completed = True
        ad_watch.watched_seconds = ad.duration  # full duration
        ad_watch.save()

        # ✅ Check if report should unlock
        completed_ads = AdWatch.objects.filter(
            user=user,
            report=report,
            completed=True
        ).count()

        unlocked = False
        ugr = UserGeneratedReport.objects.filter(user_id=request.user.id, report_id=serializer.validated_data['report_id']).last()
        ugr.ads_count=completed_ads
        if completed_ads >= 3:
            ugr.is_locked=False
            ugr.unlocked_mode="Ads"
            ugr.unlocked_on = datetime.datetime.now()
            ugr.ads_count=3
            ugr.ads_duration = AdWatch.objects.filter(user=user, report=report).aggregate(total=Sum('watched_seconds'))['total'] or 0
            ugr.credits_used=9
            ugr.save()
        unlocked = True

        return Response({
            "ad_completed": True,
            "ads_completed_count": completed_ads,
            "report_unlocked": unlocked
        })


class OfferViewsets(viewsets.GenericViewSet):
    # permission_classes = [IsAuthenticated]
    http_method_names = ["get"]

    def list(self, request, *args, **kwargs):
        user = request.user
        print(user)

        # Query raw cart items
        c = ReportMaster.objects.filter(is_deleted=True, is_active=False).last()

        # Convert queryset → list of dictionaries
        raw_data = [
            {
                "id": c.id,
                "title": c.title,
                "short_description": c.short_desc,   
            }
            
        ]

        # Create DataFrame
        df = pd.DataFrame(raw_data)

        if df.empty:
            return Response({
                "status": True,
                "message": "Dataset is empty.",
                "data": []
            })

        # Convert df → list of dictionaries
        final_output = df.to_dict(orient="records")

        return Response({
            "status": True,
            "message": "",
            "data": final_output
        })
    