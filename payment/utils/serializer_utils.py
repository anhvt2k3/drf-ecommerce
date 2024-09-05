from django.db import models
from rest_framework import serializers
### SERIALIZER UTILS ###

class SerializerUtils: 
    def validate_unique_field(model : models.Model, 
                            field_name : serializers.Field, 
                            value : any,  
                            error_message : str) -> any: 
        """
            Check if a Field value is unique in its column. 
        """
        filter_kwargs = {field_name: value, 'is_deleted': False} 
        if model.objects.filter(**filter_kwargs).exists():
            raise serializers.ValidationError(error_message)
        return value

    def create_manually(input_fields: list[str],
                        model: models.Model,
                        validated_data: dict) -> models.Model:
        """
            Create an instance with fields in input_fields from validated_data.
        """
        args = {}
        for field in input_fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.save()
        return instance
    
    def create_wth_ser_fields(
            instance_class : serializers.Serializer,
                model : models.Model, 
                    validated_data : dict):
        """
            Create instance with required fields from Serialier.
        """
        fields = instance_class.fields.keys()
        args = {}
        for field in fields:
            args.update({field: validated_data.get(field)})
        instance = model.objects.create(**args)
        instance.save()
        return instance
    
    def representation_dict_formater(
                    input_fields: list[str],
                    instance : models.Model, ) -> dict:
        """
            Return a dict of {Fields: Values} given Fields from input.
            
            **Must ensure that all Fields in input_fields are JSONizeable.
            
            `id` is always included.
        """
        args = { 'id':instance.id} 
        if 'id' in input_fields: input_fields.remove('id')
        
        for field in input_fields:
            args.update({field: instance.__getattribute__(field)})
        return args
    
    def detail_dict_formater(
                    input_fields: list[str],
                    instance : models.Model, ) -> dict:
        """
            Return a dict of {Fields: Values} given Fields from input.
            
            **Must ensure that all Fields in input_fields are JSONizeable.
            
            `id` is always included.
        """
        args = { 'id':instance.id, 'created_at':instance.created_at, 'updated_at':instance.updated_at, 'description':instance.description } 
        if 'id' in input_fields: input_fields.remove('id')
        
        for field in input_fields:
            args.update({field: instance.__getattribute__(field)})
        return args
        
        
    def representation_wth_exclude(ins_model : models.Model,
                            ins_class : serializers.Serializer,
                            exclude_fields : list,
    ):
        """
            Return a dict of Fields: Values given Fields from Serializer exclude the Fields in exclude.
        """
        fields = [field for field in ins_class.get_fields().keys() if field not in exclude_fields]
        args = {'id' : ins_model.id}
        for field in fields:
            args.update({field: ins_class.__getattribute__(field)})
        return args

    def update_wth_exclude(instance_class : serializers.Serializer,
                    instance : models.Model,
                    validated_data : dict,
                    exclude_fields : list,
    ):
        """
            Update instance at the Fields that are in its Serializer exclude the Fields in exclude.
        """
        fields = [field for field in instance_class.get_fields().keys() if field not in exclude_fields]
        for field in fields:
            value = validated_data.get(field) if field in validated_data else instance.__getattribute__(field)
            instance.__setattr__(field, value)
        instance.save() 
        return instance