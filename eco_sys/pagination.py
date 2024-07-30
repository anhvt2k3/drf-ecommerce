from rest_framework.pagination import PageNumberPagination

class SmallResultPagination(PageNumberPagination):
    page_size = 10 #@ number of items on each page
    page_size_query_param = 'page_size' #@ parameter FE can used to customize page size value
    max_page_size = 50 #@ limit the value choice of customized page size

