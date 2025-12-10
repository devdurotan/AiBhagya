from django.contrib import admin
from .models import (
    UserRole,
    UserMaster,
    ReportsCategory,
    ReportMaster,
    Cart,
    OtpCode
)


# ----------------------------
# User Role Admin
# ----------------------------
@admin.register(UserRole)
class UserRoleAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_on")
    list_filter = ("is_active",)
    search_fields = ("name",)


# ----------------------------
# User Master Admin
# ----------------------------
@admin.register(UserMaster)
class UserMasterAdmin(admin.ModelAdmin):
    list_display = (
        "email", "full_name", "role", "is_active",
        "is_staff", "date_joined"
    )
    list_filter = ("is_active", "is_staff", "role", "gender")
    search_fields = ("email", "first_name", "last_name", "full_name")
    readonly_fields = ("date_joined", "updated_on")

    fieldsets = (
        ("Login Info", {
            "fields": ("email", "password")
        }),
        ("Personal Details", {
            "fields": (
                "first_name", "last_name", "full_name",
                "dob", "tob", "pob", "gender"
            )
        }),
        ("Roles & Permissions", {
            "fields": ("role", "is_active", "is_staff", "is_superuser")
        }),
        ("Important Dates", {
            "fields": ("date_joined", "updated_on")
        }),
    )


# ----------------------------
# Reports Category Admin
# ----------------------------
@admin.register(ReportsCategory)
class ReportsCategoryAdmin(admin.ModelAdmin):
    list_display = ("category", "is_active", "created_on")
    search_fields = ("category",)
    list_filter = ("is_active",)
    readonly_fields = ("created_on", "updated_on")


# ----------------------------
# Report Master Admin
# ----------------------------
@admin.register(ReportMaster)
class ReportMasterAdmin(admin.ModelAdmin):
    list_display = ("title", "report_category", "is_active", "created_on")
    search_fields = ("title",)
    list_filter = ("report_category", "is_active")
    readonly_fields = ("created_on", "updated_on")


# ----------------------------
# Cart Admin
# ----------------------------
@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ("user", "report", "quantity", "amount", "created_on")
    search_fields = ("user__email", "report__title")
    list_filter = ("created_on",)
    readonly_fields = ("created_on", "updated_on")


# ----------------------------
# OTP Code Admin
# ----------------------------
@admin.register(OtpCode)
class OtpCodeAdmin(admin.ModelAdmin):
    list_display = ("email", "code", "is_used", "created_on", "expires_on")
    search_fields = ("email", "code")
    list_filter = ("is_used",)
    readonly_fields = ("created_on",)
