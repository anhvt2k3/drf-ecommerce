from benefit.models import DefaultBenefit
from benefit.serializers import ConfigBenefitSerializer
from shop.models import Shop
from .models import *
from .utils.serializer_utils import SerializerUtils
from rest_framework import serializers

class RankSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=100)
    required_point = serializers.IntegerField()
    benefits = serializers.JSONField(default=list)
    
    def validate_name(self, value):
        if Rank.objects.filter(name=value).exists():
            raise serializers.ValidationError('Rank with this name already exists.')
        return value
    
    def validate_required_point(self, value):
        if value < 0:
            raise serializers.ValidationError('Required point should be a positive integer.')
        return value
    
    def create(self, validated_data):
        instance_class = self
        model = Rank
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
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['name','required_point'],
                instance=instance),
        }
        
class RankDetailSerializer(RankSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['name','required_point'],
                instance=instance),
        }
        
class RankConfigSerializer(serializers.Serializer):
    rank = serializers.PrimaryKeyRelatedField(queryset=Rank.objects.all())
    shop = serializers.PrimaryKeyRelatedField(queryset=Shop.objects.all())
    required_point = serializers.IntegerField(required=False)
    enabled = serializers.BooleanField(required=False)
    
    def validate_required_point(self, value):
        if value < 0:
            raise serializers.ValidationError('Required point should be a positive integer.')
        return value
    
    def validate(self, data):
        rank = data.get('rank') or (self.instance.rank if self.instance else None)
        shop = data.get('shop') or (self.instance.shop if self.instance else None)
        required_point = data.get('required_point') or (self.instance.required_point if self.instance else None)
        enabled = data.get('enabled') or (self.instance.enabled if self.instance else True)
        benefits = data.get('benefits') or (self.instance.benefits if self.instance else None)
        
        if rank and shop and RankConfig.objects.filter(rank=rank, shop=shop).exists():
            raise serializers.ValidationError('This Rank configuration for this shop already exists. Please update it instead.')
        if rank:
            required_point = required_point or rank.required_point
            benefits = benefits or rank.benefits
        if required_point:
            rankconfs = RankConfig.objects.filter(required_point=required_point, shop=shop)
            if rankconfs.exists():
                raise serializers.ValidationError(f'There is at least 1 rank configuration with this required point: {rankconfs.first().rank.name}')
        
        data['rank'] = rank
        data['shop'] = shop
        data['required_point'] = required_point
        data['enabled'] = enabled
        data['benefits'] = benefits
        # print (data)
        return data
    
    def create(self, validated_data:dict):
        # print (validated_data)
        shop = validated_data.get('shop')
        if not RankConfig.objects.filter(shop=shop.id).exists():
            validated_data['is_default'] = True
        benefits_id = validated_data.pop('benefits', None)
        
        instance_class = self
        model = RankConfig
        validated_data = validated_data
        #! Create instance with required fields from Serialier class.
        fields = validated_data.keys()
        args = {}
        for field in fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.save()
        
        ## create Benefit Configs
        serializer_ = []
        for id in benefits_id:
            default_benefit = DefaultBenefit.objects.filter(id=id).first()
            config_benefit_data = {
                'default_benefit': id,
                'rank_required': instance.id,
                'config_amount': default_benefit.benefit_value,
            }
            serializer = ConfigBenefitSerializer(data=config_benefit_data)
            serializer.is_valid(raise_exception=True)
            serializer_.append(serializer)
        try:
            [item.save() for item in serializer_]
        except Exception as e:
            raise serializers.ValidationError(str(e))          
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
        if instance.is_default: raise serializers.ValidationError('Default RankConfig cannot be deleted.')
        instance.delete()
        return instance
    
    def to_representation(self, instance):
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['required_point','enabled','is_default'],
                instance=instance),
            'benefits': ConfigBenefitSerializer(instance.configbenefit_set.all(), many=True).data,
            'rank': instance.rank.name,
            'rank_id': instance.rank.id,
            'shop': instance.shop.name,
            'shop_id': instance.shop.id,
        }
        
class RankConfigDetailSerializer(RankConfigSerializer):
    def to_representation(self, instance):
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['required_point','enabled','is_default'],
                instance=instance),
            'benefits': ConfigBenefitSerializer(instance.configbenefit_set.all(), many=True).data,
            'rank': instance.rank.name,
            'rank_id': instance.rank.id,
            'shop': instance.shop.name,
            'shop_id': instance.shop.id,
        }