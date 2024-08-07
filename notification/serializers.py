from shop.models import Buyer, Shop
from .models import *
from .utils.serializer_utils import SerializerUtils
from rest_framework import serializers

class NotificationSerializer(serializers.Serializer):
    recipient = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    type = serializers.CharField(max_length=50)
    title = serializers.CharField(max_length=100)
    message = serializers.CharField()
    link = serializers.URLField(default=None)
    read_status = serializers.BooleanField(default=False,read_only=True)
    priority = serializers.IntegerField(default=0)
    additional_data = serializers.JSONField(default=None)

    def create(self, validated_data):
        return Notification.objects.create(**validated_data)

    def update(self, instance, validated_data):
        # instance.recipient = validated_data.get('recipient', instance.recipient)
        # instance.sender = validated_data.get('sender', instance.sender)
        instance.type = validated_data.get('type', instance.type)
        instance.title = validated_data.get('title', instance.title)
        instance.message = validated_data.get('message', instance.message)
        instance.link = validated_data.get('link', instance.link)
        instance.priority = validated_data.get('priority', instance.priority)
        instance.additional_data = validated_data.get('additional_data', instance.additional_data)
        instance.save()
        return instance

    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                instance=instance,
                input_fields=['type', 'title', 'message', 'read_status', 'priority','additional_data']),
            'recipient': instance.recipient.username,
            'sender': instance.shop.name,
            }
        
class NotificationDetailSerializer(NotificationSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                instance=instance,
                input_fields=['type', 'title', 'message', 'read_status', 'priority','additional_data']),
            'recipient': instance.recipient.username,
            'sender': instance.shop.name,
            }