from django.db import models
from django.shortcuts import get_object_or_404
from rest_framework import serializers, response
from rest_framework.status import HTTP_400_BAD_REQUEST, HTTP_200_OK, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND, HTTP_201_CREATED
from .serializer_utils  import SerializerUtils
from eco_sys.model_utils import ModelUtils
from rest_framework import generics, status, mixins, filters, pagination
from django_filters import exceptions
from django_filters.rest_framework import DjangoFilterBackend

from product.serializers import ProductSerializer

### VIEWS UTILS ###

class ViewUtils:
    
    def paginated_get_response(
                view_instance : generics.GenericAPIView,
                request,
                serializer_class : serializers.Serializer, 
                items : models.QuerySet, success=True, status_code=status.HTTP_200_OK):
        try:
            paginator = view_instance.pagination_class()
            queryset = view_instance.filter_queryset(items)
            serializer = serializer_class(paginator.paginate_queryset(queryset, request), many=True)
        except ValueError as e:
            return ViewUtils.gen_response(success=False, status=HTTP_400_BAD_REQUEST, message='BAD_REQUEST', data=str(e))
        
        currentpage = paginator.page.number if paginator.page else None
        message = f"Get Page {currentpage} successfully"
        return {
            "success": success,
            "status": status_code,
            "message": message,
            "total_Items": queryset.count(),
            "next_Page": paginator.page.next_page_number() if paginator.page and paginator.page.has_next() else None,
            "previous_Page": paginator.page.previous_page_number() if paginator.page and paginator.page.has_previous() else None,
            "current_Page": currentpage,
            "total_Pages": paginator.page.paginator.num_pages if paginator.page else None,
            "limit": paginator.page.paginator.per_page if paginator.page else None,
            "data": serializer.data,
            }
        
    def simple_create(viewins: generics.GenericAPIView, request, *args, **kwargs):
        """
            Create an instance of a model.
            
            **Require authentication.**
            
            `request.data` = { ...required_fields... }
        """
        serializer = viewins.serializer_class(data=request.data)
        if not serializer.is_valid():
            return serializer.errors, serializer
        serializer.save()
        return None, serializer
        
    def gen_response(success=False,
                    status=HTTP_400_BAD_REQUEST,
                    message='BAD_REQUEST',
                    data : serializers.Serializer.errors = None):
        return {
            "success": success,
            "status": status,
            "message": message,
            "data": data
        }
        
    def simple_retrieve(model_class : models.Model,
                        serializer_class : serializers.Serializer,
                        *args, **kwargs):
        """
            Retrieve an instance having its PK in kwargs.
        """
        pk = kwargs.get('pk')
        try:
            obj = model_class.objects.get(pk=pk, is_deleted=False)
            serializer = serializer_class(obj)
            return None, serializer.data
        except model_class.DoesNotExist:
            return {"nonexistence: Called item is not existing!"}, None
        
    def simple_list(model_class : models.Model,
                    serializer_class : serializers.Serializer,
                    *args, **kwargs):
        instnces = model_class.objects.all()
        serializer = serializer_class(instnces, many=True)
        return None, serializer.data

    def update_by_id(updates: list[dict],
                    item_model: models.Model,
                    item_serializer: serializers.Serializer):
        """
            Update the existed instances by their ids. There should be an id in every dict in updates
            Can be used for creating data (all required fields must be provided)        
            
            **Require authentication.**
            
            `updates` : [{ id, ...update_fields... }]
        """
        error = None
        serial = []
        for update in updates:
            try:
                item = item_model.objects.get(id=update.get('id'), is_deleted=False)
                serializer = item_serializer(item, data=update, partial=True)
                if not serializer.is_valid():
                    return serializer.errors, serializer
                else:
                    serial.append(serializer)
            except item_model.DoesNotExist:
                return {'non_existence': 'Thực thể được gọi không tồn tại.'}, serializer
            except serializers.ValidationError as e:
                return {"validation error": e.detail}, serializer
        #todo hong duoc
        [instance.save() for instance in serial]
        return None, serializer

    def create_per_table(request,
                        table_model: models.Model,
                        item_model: models.Model,
                        item_serializer: serializers.Serializer,
                    **kwargs) -> response.Response:
        """
            Create Objects that belong to a Table that is unique to each User.
            
            **Require authentication.**
            
            `request.data` = { ...required_fields... } or { items: [{ ...required_fields... }] }
        """
        user = request.user
        serial = []
        if 'pk' in kwargs:
            try:
                table_instance = get_object_or_404(table_model, id=kwargs.get('pk'), is_deleted=False)
            except table_model.DoesNotExist:
                return {"non_existence" : "Thực thể được gọi không tồn tại."}, table_instance
        elif 'isNew' in kwargs:
            table_instance = table_model.objects.create(user=user)
        else:
            table_instance, isCreated = table_model.objects.get_or_create(user=user, is_deleted=False)
            table_instance.save()
        datas = request.data.get('items') if 'items' in request.data and isinstance(request.data.get('items'), list) else [request.data]
        for data in datas:
            try:
                serialize_data = {get_target_field(item_model, table_model): table_instance.id, 
                                        **data}
                serializer = item_serializer(data=serialize_data)
                if not serializer.is_valid():
                    return serializer.errors, serializer
                serial.append(serializer)
            except serializers.ValidationError as e:
                return e.detail, serializer
        [instance.save() for instance in serial]
        return None, table_instance.id
    
    
    def delete_per_table(request, kwargs,
                        item_model: models.Model,
                        table_model: models.Model
                        ) -> None | dict[str, str]:
        """
            1 invalid item immediately return an error.
        """
        user = request.user
        instances = []
        if 'pk' in kwargs:
            _updates = [{ 'id': kwargs.get('pk') }]
            authorize_errors, updates = ViewUtils.check_item_authorize(_updates, user, item_model)
            if updates:
                instance = get_object_or_404(item_model ,id=updates[0]['id'], is_deleted=False)
                instances += [instance]
            else:
                return authorize_errors, updates
        else:
            table_field = get_target_field(item_model, table_model)
            table_instance = table_model.objects.get(**{'user': user})
            instances += [instance for instance in item_model.objects.filter(**{table_field: table_instance.id})]
        [instance.delete() for instance in instances]
        return None, None #! :D this is for integrity
        
    def check_item_authorize(_updates : list[dict],
                             user : models.Model,
                             item_model : models.Model):
        """
            Check if User have permission to change items.
            
            Also check for every items' existence.
            
            Cannot be used on object that is table to other objects.
        """
        updates = []
        table_field = get_field_hash_subfield_has_targetModel(item_model, user.__class__)
        for update in _updates:
            try:
                if getattr(item_model.objects.get(id=update['id']),table_field).user != user:
                    return {'unauthorized': 'Không có quyền thực hiện thao tác này.'}, update
                else:
                    updates.append(update)
            except item_model.DoesNotExist:
                return {f"Item {update['id']} không tồn tại !"}, update
            
        return None, updates
    
    def gen_errors_from_errors(**kwargs) -> dict:
        """
            Generate errors from errors.
            
            Should not being used anywhere now.
        """
        errors = {}
        for key, value in kwargs.items():
            errors.update({key: value}) if value else None
        return {'errors': errors}, None
    
    
    def list_product_mostly_in(item_model: models.Model):
        """
            Return a list of products that are mostly in the item_model.
            
            This should be replaced by the count of viewitems, cartitems... in the model and the ordering of filter Backend.
        """
        from django.db.models import Count
        item_model_name = item_model.__name__.lower()
        table_name = item_model_name.split('item')[0]
        raw_sql = f"""
            SELECT {table_name}_{table_name}item.id, {table_name}_{table_name}item.product_id, COUNT({table_name}_{table_name}item.product_id) as count
            FROM {table_name}_{table_name}item
            GROUP BY {table_name}_{table_name}item.product_id
            HAVING is_deleted = 0
            ORDER BY count DESC;
        """
        ordered_orderitems = item_model.objects.raw(raw_sql)
        
        return {
            f"top {table_name}ed items": [
                {
                    f'times {table_name}ed': item.count,
                    'product': ProductSerializer(item.product).data
                }
                        for item in ordered_orderitems]
        }




















### UTILS within UTILS ###

def get_target_field(model : models.Model,
                    target_model : models.Model) -> str | None:
    """
        Get the field name of the field that point to the target model.
    """
    for field in model._meta.get_fields():
        if field.related_model == target_model:
            return field.name
    return None

def get_field_hash_subfield_has_targetModel(base_model : models.Model, target_model : models.Model) -> str | None:
    """
        base_model          
        
        base_model.fields   -> sub_model(target?)   
        
                                sub_model.fields     -> target_model(target?)
    """
    
    for field in base_model._meta.get_fields():
        if field.related_model == target_model:
            return field.name
        if field.related_model:
            subfields = field.related_model._meta.get_fields()
            for subfield in subfields:
                if subfield.related_model == target_model:
                    return f'{field.name}'

