from django.utils import timezone
from .models import *
from .utils.utils import *
from eco_sys.permissions import IsMerchant

from user.models import User
from product.models import Product

class ViewItemSerializer(serializers.Serializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    view = serializers.PrimaryKeyRelatedField(queryset=View.objects.all())
    
    def validate_view(self, value):
        """
            Ensure the view exists.
        """
        if not View.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Không tồn tại view.")
        return value

    def validate_product(self, value):
        """
            Ensure the product exists.
        """
        if not Product.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Không tồn tại sản phẩm.")
        return value

    def validate(self, data):
        """
            Ensure there are no duplicate ViewItem instances for the same view and product.
        """
        return data
    
    def create(self, validated_data):
        product = validated_data.get('product')
        view = validated_data.get('view') if 'view' in validated_data else self.instance.view
        viewitem = ViewItem.objects.filter(view=view, product=product).first()
        if viewitem: #@ update updated_at if viewitem exists
            viewitem.updated_at = timezone.now()
            viewitem.save()
            return viewitem
            # raise serializers.ValidationError(f"Sản phẩm {product.name}({product.id}) đã có trong view.")
        
        input_fields=['view', 'product']
        model=ViewItem
        validated_data=validated_data
        ## Create instance with fields in input_fields
        args = {}
        for field in input_fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.save()
        return instance
    
    def update(self, instance, validated_data):
        instance = instance
        validated_data = validated_data
        exclude_fields = ['created_at','is_deleted','id']
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
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=[],
                instance=instance),
            'product_name': instance.product.name,
            'product_id': instance.product.id,
        }

class ViewItemDetailSerializer(ViewItemSerializer):
    def to_representation(self, instance):
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=[],
                instance=instance),
            'product_name': instance.product.name,
            'product_id': instance.product.id,
        }

class ViewSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    def create(self, validated_data):
        instance_class=self
        model=View
        validated_data=validated_data
        ## Create with required fields from Serialier class.
        fields = instance_class.fields.keys()
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
        #@ cascade delete viewitems
        [viewitem.delete() for viewitem in instance.viewitem_set.all()]
        instance.delete()
        return instance
    
    def to_representation(self, instance):
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=[],
                instance=instance),
            'user': instance.user.username,
        #@ viewitem_set is magic 
            'view_items': len(instance.viewitem_set.all()),
        }
        
class ViewDetailSerializer(ViewSerializer):
    def to_representation(self, instance):
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=[],
                instance=instance),
            'user': instance.user.username,
        #@ viewitem_set is magic 
            'view_items': len(instance.viewitem_set.all()),
        }
