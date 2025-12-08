import random
from datetime import timedelta

from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.conf import settings

from rest_framework import viewsets, status, permissions
from rest_framework.response import Response

from rest_framework_simplejwt.tokens import RefreshToken
from ..serializers.otp_serializers import OtpVerifySerializer

from ..models import Cart, UserMaster, OtpCode, ReportsCategory, ReportMaster
from ..serializers.app_serializers import AddToCartSerializer, UserRegistrationSerializer
from ..serializers.admin_serializers import ReportsCategorySerializer, ReportMasterSerializer
from rest_framework.permissions import IsAuthenticated

from django.db import transaction
import pandas as pd

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
    http_method_names = ['post']
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        payload = request.data

        # Allow single object ⇒ wrap inside a list
        if isinstance(payload, dict):
            payload = [payload]

        # Validate payload is a non-empty list
        if not isinstance(payload, list) or len(payload) == 0:
            return Response({
                "status": False,
                "message": "Invalid payload. Must be list of objects.",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST)

        success_items = []
        error_items = []

        for index, item in enumerate(payload):
            serializer = AddToCartSerializer(data=item)
            if not serializer.is_valid():
                error_items.append({
                    "index": index,
                    "payload": item,
                    "errors": serializer.errors
                })
                continue

            report_id = serializer.validated_data["id"]
            quantity = serializer.validated_data.get("quantity", 1)

            # 1️⃣ Validate report exists
            try:
                report = ReportMaster.objects.get(id=report_id)
            except ReportMaster.DoesNotExist:
                error_items.append({
                    "index": index,
                    "payload": item,
                    "errors": {"id": "Report not found"}
                })
                continue

            # 2️⃣ Create or update cart
            cart_obj, created = Cart.objects.get_or_create(
                user=request.user,
                report=report,
                defaults={"quantity": quantity}
            )

            if not created:
                cart_obj.quantity += quantity
                cart_obj.save()

            success_items.append({
                "cart_id": cart_obj.id,
                "report_id": report.id,
                "title": report.title,
                "quantity": cart_obj.quantity
            })

        return Response({
            "status": True if success_items else False,
            "message": "Cart updated successfully." if success_items else "No items added.",
            "data": {
                "success": success_items,
                "errors": error_items
            }
        }, status=status.HTTP_200_OK)




# cart details viewSet
class CartDetailsApiViewSet(viewsets.GenericViewSet):
    permission_classes = [IsAuthenticated]
    http_method_names = ["get"]

    def list(self, request, *args, **kwargs):
        user = request.user

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