from exchange.models import PointExchange
from .models import *
from .utils.utils import *

from email.policy import default
from product.models import Product
from .tasks import loyalty_logics,apply_benefit
import threading


class OrderSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    total_charge = serializers.FloatField(default=0.00, read_only=True)
    final_charge = serializers.FloatField(default=0.00, read_only=True)
    status = serializers.ChoiceField(choices=ORDER_STATUS_CHOICES, default='pending')
    coupon = serializers.PrimaryKeyRelatedField(queryset=Coupon.objects.all(), required=False)
    
    def validate(self, data):
        if self.instance and self.instance.status != 'pending':
            raise serializers.ValidationError('Order đã được xác nhận, không thể thay đổi thông tin!')
        # print (f'data: {data}')
        return data
    
    def validate_coupon(self, value):
        if value: 
            if (exchange_record := PointExchange.objects.filter(coupon=value.id).first()):
                print ('remain usage:', exchange_record.remain_usage)
                if exchange_record.remain_usage <= 0:
                    raise serializers.ValidationError('Coupon is out of usage!')
            else:
                raise serializers.ValidationError('Coupon is not in User possession!')
        return value
    
    def create(self, validated_data):
        input_fields = ['user', 'coupon']
        model = Order
        validated_data = validated_data
        ## create_manually
        args = {}
        for field in input_fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.save()
        
        if 'coupon' in validated_data:
            PointExchange.objects.filter(coupon=validated_data.get('coupon').id).update(remain_usage=models.F('remain_usage')-1)
        return instance     
    
    def update(self, instance :models.Model, validated_data):
        if 'coupon' in validated_data:
            raise serializers.ValidationError('Coupon should be applied on creating the Order!')
        #! apply loyalty logics 
        if 'status' in validated_data:
            if instance.status == 'pending' and validated_data.get('status') == 'processing':
                threading.Thread(target=loyalty_logics, args=(instance,)).start()

        instance = instance 
        validated_data = validated_data
        # print ('validated_data: ',validated_data)
        exclude_fields = ['id','coupon']
        #! Update instance with fields from validated_data without the exclude fields.
        instance_fields = [field.name for field in instance._meta.fields]
        fields = [field for field in validated_data.keys() if field not in exclude_fields and field in instance_fields]
        for field in fields:
            value = validated_data.get(field) if field in validated_data else instance.__getattribute__(field)
            instance.__setattr__(field, value)
        instance.save()
        
        if 'coupon' in validated_data:
            threading.Thread(target=apply_benefit, args=(instance.id,)).start()
        return instance
    
    def restore(self, instance=None):
        instance = instance or self.instance
        restore_set = [instance]
        #@ cascade restore orderitems
        related_objects = OrderItem.deleted.filter(order=instance)
        restore_set.extend([OrderItemSerializer(item) for item in related_objects])
        try:
            [item.restore() for item in restore_set]
        except Exception as e:
            raise serializers.ValidationError(e)
        return instance
    
    def delete(self, instance=None):
        instance = instance or self.instance
        if instance.status != 'pending':
            raise serializers.ValidationError('Order đã được xác nhận, không thể xóa!')
        #@ cascade delete orderitems
        [OrderItemSerializer(item).delete() for item in instance.orderitem_set.all()]
        [benefit.delete() for benefit in instance.orderbenefit_set.all()] 
        if instance.coupon:
            instance.coupon.pointexchange_set.filter(buyer__user=instance.user).update(remain_usage=models.F('remain_usage')+1)
            instance.coupon = None
        instance.delete()
        return instance
    
    def to_representation(self, instance):
        if instance.is_deleted:
            orderitems = OrderItem.deleted.filter(order=instance)
            orderbenefits = OrderBenefit.deleted.filter(order=instance)
            return {
                **SerializerUtils.representation_dict_formater(
                    ['total_charge', 'status', 'final_charge'],
                    instance=instance
                ),
                f'user [{instance.user.id}]': instance.user.username,
                'shop': orderitems.first().product.shop.name if orderitems.first() else None,
                'ordered_items': len(orderitems.all()),
                'coupon': instance.coupon.id if instance.coupon else None,
                'applied benefits': [{item.config_benefit.default_benefit.discount_type:item.config_benefit.config_amount} for item in orderbenefits],
                }
        return {
            **SerializerUtils.representation_dict_formater(
                ['total_charge', 'status', 'final_charge'],
                instance=instance
            ),
            f'user [{instance.user.id}]': instance.user.username,
            'shop': instance.orderitem_set.first().product.shop.name if instance.orderitem_set.first() else None,
            'ordered_items': len(instance.orderitem_set.all()),
            'coupon': instance.coupon.id if instance.coupon else None,
            'applied benefits': [{item.config_benefit.default_benefit.discount_type:item.config_benefit.config_amount} for item in instance.orderbenefit_set.all()],
        }
    
class OrderDetailSerializer(OrderSerializer):
    def to_representation(self, instance):
        if instance.is_deleted:
            orderitems = OrderItem.deleted.filter(order=instance)
            orderbenefits = OrderBenefit.deleted.filter(order=instance)
            return {
                **SerializerUtils.detail_dict_formater(
                    ['total_charge', 'status', 'final_charge'],
                    instance=instance
                ),
                f'user [{instance.user.id}]': instance.user.username,
                'shop': orderitems.first().product.shop.name if orderitems.first() else None,
                'ordered_items': len(orderitems.all()),
                'coupon': instance.coupon.id if instance.coupon else None,
                'applied benefits': [{item.config_benefit.default_benefit.discount_type:item.config_benefit.config_amount} for item in orderbenefits],
                }
        return {
            **SerializerUtils.detail_dict_formater(
                ['total_charge', 'status', 'final_charge'],
                instance=instance
            ),
            f'user [{instance.user.id}]': instance.user.username,
            'shop': instance.orderitem_set.first().product.shop.name if instance.orderitem_set.first() else None,
            'ordered_items': len(instance.orderitem_set.all()),
            'coupon': instance.coupon.id if instance.coupon else None,
            'applied benefits': [{item.config_benefit.default_benefit.discount_type:item.config_benefit.config_amount} for item in instance.orderbenefit_set.all()],
        }

        
class OrderUserSerializer(OrderSerializer):
    def validate(self, data):
        data = super().validate(data)
        if data.get('status') and data['status'] not in ['processing']:
            raise serializers.ValidationError('You do not have permission to apply this state yourself!')
        return data

class OrderItemSerializer(serializers.Serializer):
    #@ modify queryset to minimized access range of Entity
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all())
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField()
    price = serializers.FloatField(default=0)
    total_charge = serializers.FloatField(default=0)
    
    def validate(self, data : dict):
        #@ validate any fields that are given
        product = data.get('product') or (self.instance.product if self.instance else None)
        order = data.get('order') or (self.instance.order if self.instance else None)
        quantity = data.get('quantity') or (self.instance.quantity if self.instance else None)
        price = data.get('price')
        
        if product and order:
            if (order.orderitem_set.first() and product.shop != order.orderitem_set.first().product.shop) or (order.coupon and order.coupon.shop != product.shop):
                raise serializers.ValidationError(f'Product is not applicable for this Order! Product Shop: {product.shop.name}; Order Shop: {order.orderitem_set.first().product.shop.name}')
        if order:
            if order.status != 'pending':
                raise serializers.ValidationError('Order đã được xác nhận, không thể thay đổi sản phẩm!')
        if quantity:
            if quantity <= 0:
                raise serializers.ValidationError('Số lượng sản phẩm không hợp lệ!')
            if quantity > product.in_stock:
                raise serializers.ValidationError('Số lượng sản phẩm trong kho không đủ!')
        if price and price != product.price:
            raise serializers.ValidationError('Giá sản phẩm không hợp lệ!')
        
        if not self.instance:
            if order.coupon and order.coupon.shop != product.shop:
                raise serializers.ValidationError(f'This Product and the Order are not in the same Shop! Coupon Shop: {order.coupon.shop.name}')
            if order.orderitem_set.first() and product.shop != order.orderitem_set.first().product.shop:
                raise serializers.ValidationError(f'This Product and the Order are not in the same Shop! Order Shop: {order.orderitem_set.first().product.shop.name}')
            if OrderItem.objects.filter(order=order, product=product).exists():
                raise serializers.ValidationError(f'Sản phẩm [{product.id}] đã có trong Order!')
        
        return data
    
    #* required fields: product, quantity, order
    def create(self, validated_data : dict):
        product = Product.objects.filter(id=validated_data.get('product').id).first()
        order = Order.objects.filter(id=validated_data.get('order').id).first()
        quantity = validated_data.get('quantity')
        
        validated_data['price'] = product.price
        validated_data['total_charge'] = validated_data.get('price') * quantity
        # print (f'Before: product[{product.id}]newstock={product.in_stock}; Order[{order.id}]newTC={order.total_charge}')
        product.in_stock = product.in_stock - validated_data.get('quantity')
        order.final_charge = order.total_charge = float(order.total_charge) + validated_data.get('total_charge')
        # print ('-create: total charge', order.total_charge)
        # print (f'After: product[{product.id}]newstock={product.in_stock}; Order[{order.id}]newTC={order.total_charge}')
        product.save()
        order.save()
        # print (f'After save: product[{product.id}]newstock={product.in_stock}; Order[{order.id}]newTC={order.total_charge}')
        
        input_fields = ['product', 'quantity', 'price', 'total_charge', 'order']
        model = OrderItem
        validated_data = validated_data
        ## create_manually
        args = {}
        for field in input_fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.save()

        threading.Thread(target=apply_benefit, args=(instance.order.id,)).start()
        return instance        
    
    def update(self, instance : OrderItem, validated_data):
        if instance.order.status != 'pending':
            raise serializers.ValidationError('Order đã được xác nhận, không thể thay đổi sản phẩm!')
        from django.db import transaction
        with transaction.atomic():
            old_order = instance.order
            old_product = instance.product
            old_quantity = instance.quantity

            new_order = validated_data.get('order', instance.order)
            new_product = validated_data.get('product', instance.product)
            new_quantity = validated_data.get('quantity', instance.quantity)

            # Update inventory
            if old_product != new_product:
                old_product.in_stock += old_quantity
                old_product.save()
                new_product.in_stock -= new_quantity
                new_product.save()
            else:
                quantity_difference = new_quantity - old_quantity
                new_product.in_stock -= quantity_difference
                new_product.save()

            # Update OrderItem
            instance.order = new_order
            instance.product = new_product
            instance.price = new_product.price
            instance.quantity = new_quantity
            instance.save() 
            instance.reset_total_charge()
            

            # Update old order's total charge
            old_order.reset_total_charge()
            threading.Thread(target=apply_benefit, args=(old_order.id,)).start()
            # If the order has changed, update new order's total charge
            if old_order != new_order:
                new_order.reset_total_charge()
                threading.Thread(target=apply_benefit, args=(new_order.id,)).start()

        return instance
        
    def delete(self, instance=None):
        instance = instance or self.instance
        if instance.order.status != 'pending':
            raise serializers.ValidationError('Order đã được xác nhận, không thể xóa sản phẩm!')
        # details = f'newstock={instance.product.in_stock}+{instance.quantity}; newTC={instance.order.total_charge}-{instance.total_charge}'
        # raise serializers.ValidationError(detail=details)
        instance.product.in_stock += instance.quantity
        instance.order.total_charge = float(instance.order.total_charge) - float(instance.total_charge)
        instance.order.save()
        instance.product.save()
        
        instance.delete()
        return instance
    
    def restore(self, instance=None):
        instance = instance or self.instance
        if instance.product.in_stock < instance.quantity:
            raise serializers.ValidationError('Số lượng sản phẩm trong kho không đủ!')
        instance.product.in_stock -= instance.quantity
        instance.order.total_charge = float(instance.order.total_charge) + float(instance.total_charge)
        instance.order.save()
        instance.product.save()
        instance.restore()
        return instance
    
    def to_representation(self, instance):
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.representation_dict_formater(
                ['quantity', 'total_charge'],
                instance=instance
            ),
            'order': instance.order.id,
            'product_id': instance.product.id,
            'product_name': instance.product.name,
            'product_price': instance.product.price,
            'product_instock': instance.product.in_stock,
        }

class OrderItemDetailSerializer(OrderItemSerializer):
    def to_representation(self, instance):
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.detail_dict_formater(
                ['quantity', 'total_charge'],
                instance=instance
            ),
            'order': instance.order.id,
            'product_id': instance.product.id,
            'product_name': instance.product.name,
            'product_price': instance.product.price,
            'product_instock': instance.product.in_stock,
        }
            
            
#! FORCE DELETE SERIALIZERS
            
class OrderForceDeleteSerializer(OrderSerializer):
    def delete(self, instance=None):
        instance = instance or self.instance
        #@ cascade delete orderitems
        [OrderItemForceDeleteSerializer(item).delete() for item in instance.orderitem_set.all()]
        instance.delete()
        return instance
    
class OrderItemForceDeleteSerializer(OrderItemSerializer):
    def delete(self, instance=None):
        instance = instance or self.instance
        instance.product.in_stock += instance.quantity
        instance.order.total_charge = float(instance.order.total_charge) - float(instance.total_charge)
        instance.order.save()
        instance.product.save()
        
        instance.delete()
        return instance