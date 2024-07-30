from .models import *
from .utils.utils import *


class CategorySerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    #@ allow pointing to itself
    parent = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), allow_null=True, required=False)
    children = serializers.SerializerMethodField(read_only=True, required=False)
    
    def get_children(self, instance):
        if instance.children.exists():
            return CategorySerializer(instance.children.all(), many=True).data
        return []
    
    def create(self, validated_data):
        instance_class = self
        model = Category
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
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.representation_dict_formater(
                input_fields=['name'],
                instance=instance),
            'parent': instance.parent.name if instance.parent else None,
            'children': instance.category_set.count()
        }
class CategoryDetailSerializer(CategorySerializer):
    def to_representation(self, instance):
        #if instance.is_deleted: return {'This item is deleted.'}
        return {
            **SerializerUtils.detail_dict_formater(
                input_fields=['name'],
                instance=instance),
            'parent': instance.parent.name if instance.parent else None,
            'children': instance.category_set.count()
        }
    
class CategoryUserSerializer(CategorySerializer):
    def to_representation(self, instance):
        return {
            'name': instance.name,
            'parent': {'name': instance.parent.name, 'id': instance.parent.id} if instance.parent else None,
            'children': [child.name for child in instance.children.all()]
        }