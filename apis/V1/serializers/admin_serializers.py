from rest_framework import serializers
from ..models import Ad, ReportsCategory, ReportMaster, UserMaster


class ReportsCategorySerializer(serializers.ModelSerializer):
    """Serializer for ReportsCategory with file upload support."""
    image = serializers.ImageField(required=False, allow_null=True)

    class Meta:
        model = ReportsCategory
        fields = ('id', 'category', 'short_desc', 'desc', 'image', 'is_deleted', 'is_active', 'created_on', 'updated_on')
        read_only_fields = ('id', 'created_on', 'updated_on')

    def validate_category(self, value):
        """Ensure category name is not empty and not too short."""
        if not value or len(value.strip()) < 2:
            raise serializers.ValidationError("Category name must be at least 2 characters long.")
        return value.strip()

    def validate_image(self, value):
        """Validate image file size (max 5MB)."""
        if value and value.size > 5 * 1024 * 1024:  # 5MB
            raise serializers.ValidationError("Image size must not exceed 5MB.")
        return value

    def validate(self, data):
        """Ensure is_active and is_deleted are not both True."""
        if data.get('is_active') and data.get('is_deleted'):
            raise serializers.ValidationError("A category cannot be both active and deleted.")
        return data


class ReportMasterSerializer(serializers.ModelSerializer):
    """Serializer for ReportMaster with file upload support."""
    report_category_name = serializers.CharField(source='report_category.category', read_only=True)
    file = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = ReportMaster
        fields = ('id', 'report_category', 'report_category_name', 'title', 'description', 'file',
                  'is_deleted', 'is_active', 'created_on', 'updated_on')
        read_only_fields = ('id', 'created_on', 'updated_on')

    def validate_title(self, value):
        """Ensure title is not empty and not too short."""
        if not value or len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        return value.strip()

    def validate_report_category(self, value):
        """Ensure the report category exists."""
        if not value or not ReportsCategory.objects.filter(id=value.id, is_deleted=False).exists():
            raise serializers.ValidationError("Selected category does not exist or is deleted.")
        return value

    def validate_file(self, value):
        """Validate file size (max 50MB)."""
        if value and value.size > 50 * 1024 * 1024:  # 50MB
            raise serializers.ValidationError("File size must not exceed 50MB.")
        return value

    def validate(self, data):
        """Ensure is_active and is_deleted are not both True."""
        if data.get('is_active') and data.get('is_deleted'):
            raise serializers.ValidationError("A report cannot be both active and deleted.")
        return data


class UserMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserMaster
        fields = ('id', 'first_name', 'last_name', 'full_name', 'email', 'is_active', 'is_deleted')



class AdSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ad
        fields = [
            'id',
            'title',
            'video',
            'duration',
            'is_active',
            'created_on'
        ]
