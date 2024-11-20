from django.urls import path
from store import views

app_name = 'store'

urlpatterns = [
    path('', views.home, name='home'),

    #  Related to Products 
    path('search/', views.search_and_filter, name='search_and_filter'),
    path('product_list/', views.list_prod, name='product_list'),
    path('product_list_by_category/<int:category_cid>/',views.product_list_by_category,name = 'product_list_by_category'),
    path('product_view/<int:product_pid>/', views.product_detailed_view, name='product_view'),

            path('shop/', views.shop, name='shop'),
    path('shop/<int:category_id>/', views.shop, name='shop_by_category'),
    path('get_price/<int:size_id>/', views.get_price, name='get_price'),
    
]
