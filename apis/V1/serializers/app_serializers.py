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
    id = serializers.IntegerField()
    quantity = serializers.IntegerField(required=False, min_value=1, default=1)


class CartDetailsSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    short_description = serializers.CharField()
    quantity = serializers.IntegerField()
    amount = serializers.FloatField()