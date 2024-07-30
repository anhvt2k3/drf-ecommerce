from product.models import Product
from shop.models import Shop
from .models import *
from .utils.serializer_utils import SerializerUtils
from rest_framework import serializers

class QuestSerializer(serializers.Serializer):
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    name = serializers.CharField(max_length=100)
    reward_point = serializers.IntegerField(default=0)
    product_range = serializers.JSONField(default=list)
    min_spent = serializers.FloatField(default=0)
    min_quantity = serializers.IntegerField(default=0)
    end_date = serializers.DateTimeField(allow_null=True, required=False)
    
    def validate(self, data):
        product_range = data.get('product_range') or (self.instance.product_range if self.instance else None)
        shop = data.get('shop') or (self.instance.shop if self.instance else None)
        if product_range:
            for product_id in product_range:
                if not Product.objects.filter(id=product_id,shop=shop).exists():
                    raise serializers.ValidationError(f"Product with id={product_id} is not valid.")
        
        return data
    
    def create(self, validated_data):
        instance_class = self
        model = Quest
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
    
    def truncate_list(self, items):
        if len(items) > 6:
            return items[:3] + ['...'] + items[-2:]
        return items
    
    def to_representation(self, instance):
        #@ this should never be true
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['name', 'reward_point', 'min_spent', 'min_quantity', 'end_date'],
                instance=instance),
            'product_range': self.truncate_list(instance.product_range), 
            'shop': instance.shop.name,
            'shop_id': instance.shop.id
        }

class QuestDetailSerializer(QuestSerializer):
    def to_representation(self, instance):
        #@ this should never be true
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['name', 'reward_point', 'min_spent', 'min_quantity', 'end_date'],
                instance=instance),
            'product_range': self.truncate_list(instance.product_range), 
            'shop': instance.shop.name,
            'shop_id': instance.shop.id
        }
        