from shop.models import Shop
from shop.serializers import ShopSerializer
from .models import User
from .utils.utils import *
from . import google
import os
from rest_framework import exceptions


class UserSerializer(serializers.Serializer):
    username = serializers.EmailField(max_length=50)
    password = serializers.CharField(max_length=255)
    
    def validate_username(self, value):
        model = User
        field_name = 'username'
        value = value
        error_message = 'Email này đã được tài khoản khác sử dụng.'
        ## validate unique field
        filter_kwargs = {field_name: value, 'is_deleted': False} 
        if model.objects.filter(**filter_kwargs).exists():
            raise serializers.ValidationError(error_message)
        return value
        
    def create(self, validated_data):
        instance_class = self
        model = User
        validated_data = validated_data
        #! Create instance with required fields from Serialier class.
        fields = validated_data.keys()
        args = {}
        for field in fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.save()
        return instance
        
    def update(self, instance, validated_data):
        instance_class = self
        instance = instance
        validated_data = validated_data
        exclude_fields = ['password']
        ## Update instance with fields from Serializer class without the exclude fields.
        fields = [field for field in instance_class.get_fields().keys() if field not in exclude_fields]
        for field in fields:
            value = validated_data.get(field) if field in validated_data else instance.__getattribute__(field)
            instance.__setattr__(field, value)
        instance.save() 
        return instance
    
    def delete(self, instance=None):
        instance = instance or self.instance
        instance.delete()
        return instance
    
    def to_representation(self, instance):
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.representation_dict_formater(
                instance=instance,
                input_fields=['username','is_staff','is_merchant'],
            ),
            'owner of shop': ShopSerializer(Shop.objects.filter(merchant=instance).first()).data if instance.is_merchant else None,
        }
class UserDetailSerializer(UserSerializer):
    def to_representation(self, instance):
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.detail_dict_formater(
                instance=instance,
                input_fields=['username','is_staff','is_merchant'],
            ),
            'owner of shop': ShopSerializer(Shop.objects.filter(merchant=instance).first()).data if instance.is_merchant else None,
        }
    
class UserLoginSerializer(serializers.Serializer):
    username = serializers.EmailField(max_length=50)
    password = serializers.CharField(max_length=50)
    
class UserMasterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = '__all__'
        
    def create(self, validated_data):
        instance_class = self
        model = User
        validated_data = validated_data
        #! Create instance with required fields from Serialier class.
        fields = validated_data.keys()
        args = {}
        for field in fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.save()
        return instance
    
    def update(self, instance :models.Model, validated_data):
        instance = instance
        validated_data = validated_data
        exclude_fields = ['id']
        #! Update instance with fields from validated_data without the exclude fields.
        instance_fields = [field.name for field in instance._meta.fields]
        fields = [field for field in validated_data.keys() if field not in exclude_fields and field in instance_fields]
        for field in fields:
            value = validated_data.get(field) if field in validated_data else instance.__getattribute__(field)
            instance.__setattr__(field, value)
        instance.save()
        return instance
        
    def delete(self, instance=None):
        instance = instance or self.instance
        instance.delete()
        return instance
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                instance=instance,
                input_fields=['username','is_staff','is_merchant'],
            )
        }
        
class UserMasterDetailSerializer(UserMasterSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                instance=instance,
                input_fields=['username','is_staff','is_merchant'],
            )
        }