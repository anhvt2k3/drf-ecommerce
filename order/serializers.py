from cart.models import Cart, CartItem
from exchange.models import PointExchange
from flashsale.models import Flashsale, FlashsaleProduct
from order.models import OrderItem
from .models import *
from .utils.utils import *

from django.db import transaction
from flashsale.tasks import calculations_N_apply_flashsale
from product.models import Product
from .tasks import loyalty_logics,apply_benefit
import threading

class FlashsaleApplySerializer(serializers.Serializer):
    flashsale = serializers.PrimaryKeyRelatedField(queryset=Flashsale.objects.all())
    
    def to_internal_value(self, data):
        # If data is a single integer, assume it's the flashsale ID and transform it
        if isinstance(data, int):
            data = {'flashsale': data}
        return super().to_internal_value(data)
    
    def validate(self, data):
        from django.utils import timezone
        
        flashsale = data.get('flashsale')
        if flashsale.start_date > timezone.now():
            raise serializers.ValidationError('Flashsale has not started yet!')
        if flashsale.end_date < timezone.now():
            raise serializers.ValidationError('Flashsale has ended!')
        return flashsale
class OrderItemSerializer(serializers.Serializer):
    #@ modify queryset to minimized access range of Entity
    order = serializers.PrimaryKeyRelatedField(queryset=Order.objects.all(), required=False)
    
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.IntegerField()
    
    price = serializers.FloatField(required=False)
    total_charge = serializers.FloatField(required=False)
    
    def validate(self, data : dict):
        #@ validate any fields that are given
        product = data.get('product') or (self.instance.product if self.instance else None)
        order = data.get('order') or (self.instance.order if self.instance else None)
        quantity = data.get('quantity') or (self.instance.quantity if self.instance else None)
        
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
        
        # if not self.instance:
            # if order.coupon and order.coupon.shop != product.shop:
            #     raise serializers.ValidationError(f'This Product and the Order are not in the same Shop! Coupon Shop: {order.coupon.shop.name}')
            # if order.orderitem_set.first() and product.shop != order.orderitem_set.first().product.shop:
            #     raise serializers.ValidationError(f'This Product and the Order are not in the same Shop! Order Shop: {order.orderitem_set.first().product.shop.name}')
            # if OrderItem.objects.filter(order=order, product=product).exists():
            #     raise serializers.ValidationError(f'Sản phẩm [{product.id}] đã có trong Order!')
        data['price'] = data.get('price', product.price) 
        data['total_charge'] = data['price'] * quantity 
        
        return data
    
    #* required fields: product, quantity, order
    def create(self, validated_data : dict) -> OrderItem:
        product = Product.objects.filter(id=validated_data.get('product').id).first()
        order = Order.objects.filter(id=validated_data.get('order').id).first()
        
        # product.in_stock = product.in_stock - validated_data.get('quantity')
        # order.final_charge = order.total_charge = float(order.total_charge) + validated_data.get('total_charge')
        # product.save()
        # order.save()
        
        input_fields = ['product', 'quantity', 'price', 'total_charge', 'order']
        model = OrderItem
        validated_data = validated_data
        ## create_manually
        args = {}
        for field in input_fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.save()

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

            # # Update old order's total charge
            old_order.reset_total_charge()
            # # If the order has changed, update new order's total charge
            if old_order != new_order:
                new_order.reset_total_charge()

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
            'sold_price': instance.price,
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
            'sold_price': instance.price,
            'product_instock': instance.product.in_stock,
        }

class OrderSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    total_charge = serializers.FloatField(default=0.00, read_only=True)
    final_charge = serializers.FloatField(default=0.00, read_only=True)
    status = serializers.ChoiceField(choices=ORDER_STATUS_CHOICES, default='pending')
    coupon = serializers.PrimaryKeyRelatedField(queryset=Coupon.objects.all(), required=False)
    flashsale = FlashsaleApplySerializer(required=False)
    
    using_cart = serializers.BooleanField(default=False)
    creating_with_items = serializers.BooleanField(default=False)
    orderitems = OrderItemSerializer(many=True) #* format: [{'product':<id>, 'quantity':<int>}]
    
    def validate(self, data):
        if self.instance and self.instance.status != 'pending':
            raise serializers.ValidationError('Order đã được xác nhận, không thể thay đổi thông tin!')
        if (coupon := data.get('coupon')): 
            if not Coupon.objects.filter(pointexchange__buyer__user=data['user'], id=coupon.id).exists():
                raise serializers.ValidationError('User does not possess this Coupon!')
            if PointExchange.objects.filter(coupon=coupon,buyer__user=data['user']).first().remain_usage <= 0:
                raise serializers.ValidationError('Coupon is out of usage!')
        if not (data.get('creating_with_items') or data.get('using_cart')):
            items = data.get('orderitems', [])
            if not items:
                raise serializers.ValidationError("Items must be provided if not using cart or creating with items.")
        # print (f'data: {data}')
        return data
    
    def create(self, validated_data):
        using_cart = validated_data.get('using_cart', False)
        creating_with_items = validated_data.get('creating_with_items', False)
        user = validated_data.get('user')
        coupon = validated_data.get('coupon')
        flashsale = validated_data.get('flashsale')
        
        if using_cart:
            cart = Cart.objects.filter(user=user).first()
            cartitems = CartItem.objects.filter(cart=cart)
            items = [{'product': item.product.id, 'quantity': item.quantity} for item in cartitems]
            # cart.delete() #! Optionally delete cart if required
        elif creating_with_items:
            items = validated_data.get('orderitems', [])
        
        #! validate items
        if not self.isNoDuplicateProduct(items):
            raise serializers.ValidationError('Duplicate Product in Order Items!')
        
        shopmap = self.bind_shopNcoupon(items=items, user=user, coupon=coupon, flashsale=flashsale)
        ordermap = self.save_to_db(shopmap)
        
        for order in ordermap.keys():
            #@ these 2 threads should not have any dependency on each other
            threading.Thread(target=loyalty_logics, args=(order,)).start()
            apply_benefit(order.id)
        
        return list(ordermap.keys())

    def bind_shopNcoupon(self, items, user, coupon, flashsale):
        """
            Creates orders per shop based on the items and returns the items with associated order IDs.
        """
        order_of = {}
        for item in items:
            shop = item['product'].shop
            if shop not in order_of.keys():
                args = {'user': user, 'coupon': coupon if coupon and coupon.shop.id == shop.id else None, 
                            'flashsale': flashsale if flashsale and flashsale.shop.id == shop.id else None, }
                order_of[shop] = (Order(**args), [])
            order_of[shop][1].append(item)
        return order_of 
    
    def isNoDuplicateProduct(self, orderitems):
        products = [item['product'] for item in orderitems]
        return len(products) == len(set(products))
    
    def save_to_db(self, ordermap):
        instmap = {}
        with transaction.atomic():
            for order, orderitems in ordermap.values():
                orderitems, order.total_charge = calculations_N_apply_flashsale(order.flashsale, orderitems, order.user, is_order=True)
                order.save()
                instmap[order] = [OrderItemSerializer().create({'order':order,**item}) for item in orderitems]
        return instmap
    
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
        exclude_fields = ['id', 'coupon']
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
        # if instance.status != 'pending':
        #     raise serializers.ValidationError('Order đã được xác nhận, không thể xóa!')
        #@ cascade delete orderitems
        [OrderItemSerializer(item).delete() for item in instance.orderitem_set.all()]
        [benefit.delete() for benefit in instance.orderbenefit_set.all()] 
        if instance.coupon:
            instance.coupon.pointexchange_set.filter(buyer__user=instance.user).update(remain_usage=models.F('remain_usage')+1)
            instance.coupon = None
        instance.delete()
        return instance
    
    def to_representation(self, instance):
        if isinstance(instance, list):
            return [self.to_representation(Order.objects.filter(id=order.id).first()) for order in instance]
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
                'promotion': instance.promotion.id if instance.promotion else None,
                'applied benefits': [item.source for item in orderbenefits],
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
            'promotion': instance.promotion.id if instance.promotion else None,
            'applied benefits': [item.source for item in instance.orderbenefit_set.all()],
        }
    
class OrderDetailSerializer(OrderSerializer):
    def to_representation(self, instance):
        if isinstance(instance, list):
            return [self.to_representation(Order.objects.filter(id=order.id).first()) for order in instance]
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
                'promotion': instance.promotion.id if instance.promotion else None,
                'applied benefits': [item.source for item in orderbenefits],
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
            'promotion': instance.promotion.id if instance.promotion else None,
            'applied benefits': [item.source for item in instance.orderbenefit_set.all()],
        }

        
class OrderUserSerializer(OrderSerializer):
    def validate(self, data):
        data = super().validate(data)
        if data.get('status') and data['status'] not in ['pending']:
            raise serializers.ValidationError('You do not have permission to apply this state yourself!')
        return data            
            
#! FORCE DELETE SERIALIZERS
class OrderForceDeleteSerializer(OrderSerializer):
    def delete(self, instance=None):
        instance = instance or self.instance
        #@ cascade delete orderitems
        [OrderItemForceDeleteSerializer(item).delete() for item in instance.orderitem_set.all()]
        [benefit.delete() for benefit in instance.orderbenefit_set.all()]
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
    
#! CHECK OUT SERIALIZERS
class CheckoutSerializer(serializers.Serializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    coupon = serializers.PrimaryKeyRelatedField(queryset=Coupon.objects.all(),required=False)
    flashsale = FlashsaleApplySerializer(required=False)
    items = OrderItemSerializer(many=True) #* format: [{'product':<id>, 'quantity':<int>}]
    
    def bind_shop(self, items:list[dict], coupon, flashsale):
        #* input format: items=[{'product':<Product>, 'quantity':<int>}], coupon=<Coupon>
        #* output format: { <shop>: {'coupon':<Coupon>, 'total_charge': <float>, 'items': [{ 'product':<Product>, 'quantity':<int>, 'price':<Product>.price, 'charge':<Product>.price*quantity }]} }
        order_of = {}
        for item in items:
            shop = item['product'].shop
            quantity = item['quantity']
            # Check if the shop is already in the dictionary
            if shop not in order_of:
                order_of[shop] = {
                    'coupon': coupon if coupon and coupon.shop == shop else None,
                    'flashsale': flashsale if flashsale and flashsale.shop == shop else None,
                    'items': [],
                    'total_charge': 0.0
                }
            # Append the item to the shop's items list
            order_of[shop]['items'].append({
                'product': item['product'],
                'quantity': quantity,
                'price': item['price'],
                'charge': item['price'] * quantity
            })
            order_of[shop]['total_charge'] += item['price'] * quantity 

        return order_of
    
    def validate(self, data):
        user = data.get('user')
        if (coupon := data.get('coupon')): 
            if not Coupon.objects.filter(pointexchange__buyer__user=user, id=coupon.id).exists():
                raise serializers.ValidationError('User does not possess this Coupon!')
            if PointExchange.objects.filter(coupon=coupon,buyer__user=user).first().remain_usage <= 0:
                raise serializers.ValidationError('Coupon is out of usage!')
        
        from . import tasks
        from flashsale import tasks as flashsale_tasks
        items = data.get('items')
        binded_items = self.bind_shop(items, data.get('coupon'), data.get('flashsale'))
        for shop in binded_items.keys():
            binded_items[shop]['user'] = user
            if flashsale := binded_items[shop]['flashsale']:
                binded_items[shop]['items'], binded_items[shop]['total_charge'] = flashsale_tasks.calculations_N_apply_flashsale(flashsale, binded_items[shop]['items'], user)
                promo = binded_items[shop]['promotion'] = None
            else:
                promo = binded_items[shop]['promotion'] = tasks.get_promo(user, cart=(shop, binded_items[shop]['items']))
            binded_items[shop]['final_charge'] = tasks.apply_discounts(
                benefits=tasks.retrieve_discounts(user, shop, coupon=binded_items[shop]['coupon'],promo=promo),
                total_charge=binded_items[shop]['total_charge']
            )   
        return binded_items
    
    def to_representation(self, instance):
        """
        {
            Checkout <i>: {
                "shop": <Shop.name>,
                "sub_total": <total_charge>,
                "total": <final_charge>,
                "items": [
                    {
                        "product": <Product>.name,
                        "price": <float>,
                        "quantity": <int>,
                        "total_charge": <float>
                    },...
                ]
            }, ...
        }
        """
        representation = {}
        i = 1

        for shop, data in self.validated_data.items(): #@ dict(zip(shop, data)) can be used to reverse the effect of self.validated_data.items()
            items_representation = []
            for item in data['items']:
                items_representation.append({
                    'product': item['product'].name,
                    'product_id': item['product'].id,
                    'price': item['price'],
                    'non-sale_price': item['product'].price,
                    'quantity': item['quantity'],
                    'total_charge': item['charge']
                })
            buyer = data['user'].buyer_set.filter(shop=shop).first()
            representation[f'Checkout {i}'] = {
                'shop': shop.name,
                'user rank': buyer.rank.rank.name if buyer else None,
                'items': items_representation,
                'sub_total': data['total_charge'],
                'coupon': data['coupon'].id if data['coupon'] else None,
                'promotion': data['promotion'].id if data['promotion'] else None,
                'flashsale': data['flashsale'].id if data['flashsale'] else None,
                'total': data.get('final_charge', data['total_charge']),
            }
            
            i += 1

        return representation

