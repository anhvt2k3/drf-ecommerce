
from order.models import Order
from user.models import User
from .models import *
from .utils.serializer_utils import SerializerUtils
from rest_framework import serializers

class RefundSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    cause = serializers.CharField()
    contacts = serializers.DictField()
    
    def validate_order(self, value):
        if value.status == 'delivered':
            raise serializers.ValidationError("Order has been delivered, cannot refund.")
        if value.status != 'paid':
            raise serializers.ValidationError("Order has not been paid, cannot refund.")
        for refund in Refund.objects.filter(order=value):
            if refund.confirmation:
                raise serializers.ValidationError("Order has been approved.")
        return value
    
    def validate_contacts(self, value):
        ## expecting contacts format as
        ## {
        ##     "phone": <phone-num>,
        ##     "email": <email>,
        ##     "address": <address>
        ## }
        for key in value.keys():
            if key == 'email':
                serializers.EmailField().run_validation(value[key])
            elif key == 'phone':
                serializers.RegexField(regex=r'^(84|0[35789])[0-9]{8}\b').run_validation(value[key])
            elif key == 'address':
                serializers.CharField().run_validation(value[key])
        return value

    def validate(self, data):
        if data['order'].user != data['user']:
            raise serializers.ValidationError("User has no right to refund this order.")
        return data
    
    def create(self, validated_data):
        validated_data.pop('user')
        return Refund.objects.create(**validated_data)
    
    def delete(self, instance=None):
        instance = instance or self.instance
        instance.delete()
        return instance
    
    def to_representation(self, instance):
        return {
            'id': instance.id,
            'created_at': instance.created_at,
            'order': instance.order.id,
            'user': instance.order.user.id,
            'username': instance.order.user.username,
            'cause': instance.cause,
            'confirmation': instance.confirmation,
            **({'receipt': instance.order.refundd} if instance.confirmation else {}) ,
        }

class RefundDetailSerializer(RefundSerializer):
    def to_representation(self, instance):
        from order.serializers import OrderSerializer
        from user.serializers import UserSerializer
        return {
            **SerializerUtils.detail_dict_formater(
                ['cause', 'contacts', 'confirmation'],
                instance),
            'order': OrderSerializer(instance.order).data,
            'user': UserSerializer(instance.order.user.id).data,
            **({'receipt': instance.order.refundd} if instance.confirmation else {}) ,
        }
