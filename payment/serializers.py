from user.models import User
from user.serializers import UserDetailSerializer
from .models import *
from .utils.serializer_utils import SerializerUtils
from rest_framework import serializers

class PaymentSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    method_object = serializers.JSONField(default=dict)
    
    def validate(self, data):
        ## validate for correct Payment Method object here
        return data
    
    def create(self, validated_data):
        type = validated_data.get('method_object').get('type')
        return Payment.objects.create(**{'type':type, **validated_data})
    
    def update(self, instance, validated_data):
        instance.user = validated_data.get('user', instance.user)
        instance.type = validated_data.get('type', instance.type)
        instance.method_object = validated_data.get('method_object', instance.method_object)
        instance.save()
        return instance
    
    def to_representation(self, instance):
        return {
            'id': instance.id,
            'user_id': instance.user.id,
            'user': instance.user.username,
            'type': instance.type,
            'brand': instance.method_object.get(instance.type).get('brand'),
        }
        
class PaymentDetailSerializer(PaymentSerializer):
    def to_representation(self, instance):
        return {
            'id': instance.id,
            'user': UserDetailSerializer(instance.user).data,
            'type': instance.type,
            'brand': instance.method_object.get(instance.type).get('brand'),
        }