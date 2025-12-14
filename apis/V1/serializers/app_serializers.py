from rest_framework import serializers
from ..models import UserMaster


class UserRegistrationSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    first_name = serializers.CharField(required=True, allow_blank=False)
    last_name = serializers.CharField(required=True, allow_blank=False)
    dob = serializers.DateField(required=True)
    tob = serializers.TimeField(required=True)
    pob = serializers.CharField(required=True, allow_blank=False)
    gender = serializers.CharField(required=True, allow_blank=False)

    class Meta:
        model = UserMaster
        fields = ('first_name', 'last_name', 'email', 'dob', 'tob', 'pob', 'gender')

    def create(self, validated_data):
        user = UserMaster.objects.create_user(**validated_data)
        return user



# #---------add to cart serializer---
class AddToCartSerializer(serializers.Serializer):
    report_id = serializers.IntegerField()
    


class CheckCartSerializer(serializers.Serializer):
    cart_id = serializers.IntegerField()

class GlobalSerializer():
    pass