from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('products/<int:pk>/', views.product_detail, name='product_detail'),
    path('products/<int:pk>/payment/', views.payment_view, name='payment'),
    path('orders/success/<int:pk>/', views.order_success, name='order_success'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('admin-panel/orders/', views.ManageOrdersView.as_view(), name='manage_orders'),
    path('admin-panel/products/', views.ManageProductsView.as_view(), name='manage_products'),
    path('admin-panel/products/add/', views.ProductCreateView.as_view(), name='product_add'),
    path('admin-panel/products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('admin-panel/products/<int:pk>/delete/', views.ProductDeleteView.as_view(), name='product_delete'),
    path('admin-panel/categories/', views.ManageCategoriesView.as_view(), name='manage_categories'),
    path('admin-panel/categories/add/', views.CategoryCreateView.as_view(), name='category_add'),
    path('admin-panel/categories/<int:pk>/delete/', views.CategoryDeleteView.as_view(), name='category_delete'),
]
