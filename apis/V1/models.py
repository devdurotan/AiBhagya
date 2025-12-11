from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin

from .managers import UserManager


class UserRole(models.Model):

    ROLE_CHOICES = (
        ("ADMIN", "ADMIN"),
        ("USER", "USER"),
    )

    name = models.CharField(max_length=50, choices=ROLE_CHOICES, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.get_name_display()  # Shows "Admin" instead of "admin"


class UserMaster(AbstractBaseUser, PermissionsMixin):

    GENDER_CHOICES = (
        ('MALE', 'MALE'),
        ('FEMALE', 'FEMALE'),
        ('OTHER', 'OTHER'),
    )

    email = models.EmailField(unique=True)
    username = models.CharField(max_length=150, blank=True, null=True)
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    full_name = models.CharField(max_length=300, blank=True, null=True)

    dob = models.DateField(blank=True, null=True)   # ✔ Date field
    tob = models.TimeField(blank=True, null=True)   # ✔ Time field
    pob = models.CharField(max_length=300, blank=True, null=True)

    gender = models.CharField(
        max_length=10,
        choices=GENDER_CHOICES,
        blank=True,
        null=True
    )  # ✔ Choice field

    role = models.ForeignKey(
        UserRole,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='role_id'
    )

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    date_joined = models.DateTimeField(default=timezone.now)
    updated_on = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def save(self, *args, **kwargs):
        self.full_name = f"{self.first_name} {self.last_name}".strip()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.email

class ReportsCategory(models.Model):
	category = models.CharField(max_length=255)
	short_desc = models.TextField(blank=True, null=True)
	desc = models.TextField(blank=True, null=True)
	# Image field for category
	image = models.ImageField(upload_to='categories/', blank=True, null=True)
	is_deleted = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)
	created_on = models.DateTimeField(auto_now_add=True)
	updated_on = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.category 


class ReportMaster(models.Model):
	report_category = models.ForeignKey(ReportsCategory, on_delete=models.CASCADE, related_name='reports')
	title = models.CharField(max_length=255)
	description = models.TextField(blank=True, null=True)
	# File field for report attachments
	file = models.FileField(upload_to='reports/', blank=True, null=True)
	is_deleted = models.BooleanField(default=False)
	is_active = models.BooleanField(default=True)
	created_on = models.DateTimeField(auto_now_add=True)
	updated_on = models.DateTimeField(auto_now=True)

	def __str__(self):
		return self.title


class Cart(models.Model):
    report = models.ForeignKey(ReportMaster, on_delete=models.CASCADE, related_name='carts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='carts')
    quantity = models.PositiveIntegerField(default=1)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    amount = models.IntegerField(default=0,null=True,blank=True)

    class Meta:
        unique_together = (('report', 'user'),)

    def __str__(self):
        return f"Cart(user={self.user}, report={self.report}, qty={self.quantity})"


class OtpCode(models.Model):
    """Store OTP codes associated with an email address (or user).
    We keep email as primary association so OTPs can be sent to unregistered emails.
    """
    email = models.EmailField()
    code = models.CharField(max_length=10)
    created_on = models.DateTimeField(auto_now_add=True)
    expires_on = models.DateTimeField(null=True, blank=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Otp(email={self.email}, code={self.code})"
    

class UserReports(models.Model):
    report_category = models.ForeignKey(
        ReportsCategory,
        on_delete=models.CASCADE,
        related_name='reports_cat'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='report_user'
    )

    report_id = models.ForeignKey(
         ReportMaster,
        on_delete=models.CASCADE,
        related_name='report_master')
    
    content = models.TextField(blank=True, null=True)

    # Status flags
    is_locked = models.BooleanField(default=False,null=True,blank=True)
    is_paid = models.BooleanField(default=False,null=True,blank=True)
    is_viewed_ads = models.BooleanField(default=False,null=True,blank=True)

    # Ads
    no_of_ads = models.IntegerField(default=0,null=True,blank=True)
    ad_duration = models.IntegerField(default=0,null=True,blank=True)  # seconds or minutes (you decide)

    # Default flags
    is_deleted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.report_id} - {self.user.email}"


class Payments(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payments'
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    no_of_report = models.PositiveIntegerField(default=0,null=True,blank=True)

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Payment(user={self.user.email}, amount={self.amount})"

