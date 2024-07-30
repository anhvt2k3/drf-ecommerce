from .models import *
from user.models import User

from product.models import Product
from product.serializers import ProductSerializer

from .utils.utils import *



    
class CartItemSerializer(serializers.Serializer):
    cart = serializers.PrimaryKeyRelatedField(queryset=Cart.objects.all())
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    price = serializers.FloatField(read_only=True)
    quantity = serializers.IntegerField()
    
    def validate_cart(self, data : Cart):
        """
            Ensure the cart exists.
        """
        value = data
        if not Cart.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Giỏ hàng không tồn tại.")
        return value

    def validate_product(self, data : Product):
        """
            Ensure the product exists.
        """
        value = data
        if not Product.objects.filter(id=value.id).exists():
            raise serializers.ValidationError(f"Sản phẩm id={value.id} không tồn tại.")
        return value

    def validate_quantity(self, value):
        """
            Ensure that the quantity is positive and does not exceed available stock.
        """
        if value <= 0:
            raise serializers.ValidationError("Số lượng phải là số dương.")
        return value

    def validate(self, data : dict):
        """
            Ensure there are no duplicate CartItem instances for the same cart and product.
        """
        product = data.get('product')
        quantity = data.get('quantity')
        cart = data.get('cart') if data.get('cart') else self.instance.cart
        if quantity > product.in_stock:
            raise serializers.ValidationError(f"Số lương vượt quá số lượng có sẵn của {product.name}[{product.id}].")
        if CartItem.objects.filter(cart=cart, product=product).exists():
            raise serializers.ValidationError(f"Sản phẩm {product.name}[{product.id}] đã có trong giỏ hàng.")
        return data
    
    def create(self, validated_data):
        price = Product.objects.get(id=validated_data.get('product').id).price
        validated_data.update({'price': price})
        
        input_fields=['cart', 'product', 'quantity', 'price']
        model=CartItem
        validated_data=validated_data
        ## create_manually
        args = {}
        for field in input_fields:
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
    
    def restore(self, instance=None):
        instance = instance or self.instance
        instance.restore()
        return instance
    
    def to_representation(self, instance):
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['quantity', 'price'],
                instance=instance),
            'product_name': instance.product.name,
            'product_id': instance.product.id,
            'cart_of': instance.cart.user.username
        }
        
class CartItemDetailSerializer(CartItemSerializer):
    def to_representation(self, instance):
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['quantity', 'price'],
                instance=instance),
            'product_name': instance.product.name,
            'product_id': instance.product.id,
            'cart_of': instance.cart.user.username
        }


class CartSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    
    def validate_user(self, value):
        """
            Ensure the user exists.
        """
        if not User.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("Người dùng không tồn tại")
    
    def create(self, validated_data):
        instance_class = self,
        model = Cart, 
        validated_data = validated_data
        ## create by ser fields
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
        #@ cascade delete cartitems
        [item.delete() for item in instance.cartitem_set.all()]
        instance.delete()
        return instance
    
    def restore(self, instance=None):
        instance = instance or self.instance
        restore_set = [instance]
        related_objects = []
        for related_object in instance._meta.related_objects:
            related_manager_name = related_object.get_accessor_name()
            related_manager = getattr(instance, related_manager_name)
            if hasattr(related_manager.model, 'deleted'):
                deleted_objects = related_manager.model.deleted.filter(**{related_manager.field.name: instance})
                related_objects.extend(deleted_objects)
        restore_set.extend(related_objects)
        [item.restore() for item in restore_set]
        return instance
    
    def to_representation(self, instance):
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=[], 
                instance=instance),
            'user': instance.user.username,
            'cart_items': len(instance.cartitem_set.all())
        }
        
class CartDetailSerializer(CartSerializer):
    def to_representation(self, instance):
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=[], 
                instance=instance),
            'user': instance.user.username,
            'cart_items': len(instance.cartitem_set.all())
        }