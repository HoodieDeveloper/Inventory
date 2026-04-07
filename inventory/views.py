from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db import transaction
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from .blob_utils import ProductImageUploadError, delete_product_image, upload_product_image
from .forms import LoginForm, PaymentForm, ProductForm, PurchaseForm, SignUpForm
from .models import Category, Order, Product


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'admin'

    def handle_no_permission(self):
        messages.error(self.request, 'Only admin users can access admin tools.')
        return redirect('home')


class ManageOrdersView(AdminRequiredMixin, ListView):
    template_name = 'inventory/manage_orders.html'
    model = Order
    context_object_name = 'orders'

    def get_queryset(self):
        return Order.objects.select_related('customer', 'product', 'product__category').all()


def get_safe_next_url(request):
    next_url = request.POST.get('next') or request.GET.get('next')
    if next_url and url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
        return next_url
    return reverse('home')


def login_redirect_for(next_url):
    return f"{reverse('login')}?next={next_url}"


def require_customer_access(request, next_url):
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in or sign up before continuing.')
        return redirect(login_redirect_for(next_url))
    if request.user.role != 'customer':
        messages.error(request, 'Only customer accounts can buy products. Admin accounts can review order records.')
        return redirect('manage_orders' if request.user.role == 'admin' else 'home')
    return None


def checkout_session_key(product_id):
    return f'checkout_product_{product_id}'


def home(request):
    categories = Category.objects.annotate(product_count=Count('products'))
    products = Product.objects.select_related('category').all()
    category_id = request.GET.get('category')

    if category_id and category_id.isdigit():
        products = products.filter(category_id=category_id)

    context = {
        'categories': categories,
        'products': products,
        'selected_category': category_id or '',
    }
    return render(request, 'inventory/home.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = LoginForm(request.POST or None)
    next_url = get_safe_next_url(request)

    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['password']
        user = authenticate(request, username=email, password=password)

        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.full_name}!')
            return redirect(next_url)

        messages.error(request, 'Invalid email or password.')

    return render(request, 'inventory/login.html', {'form': form, 'next': next_url})


def signup_view(request):
    if request.user.is_authenticated:
        return redirect('home')

    form = SignUpForm(request.POST or None)
    next_url = get_safe_next_url(request)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        messages.success(request, f'Account created successfully. Welcome, {user.full_name}!')
        return redirect(next_url)

    return render(request, 'inventory/signup.html', {'form': form, 'next': next_url})


def logout_view(request):
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('home')


def product_detail(request, pk):
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk)
    next_url = reverse('product_detail', args=[product.pk])

    if not request.user.is_authenticated:
        messages.info(request, 'Please log in first to buy this product.')
        return redirect(login_redirect_for(next_url))

    is_customer = request.user.role == 'customer'
    form = PurchaseForm(request.POST or None, product=product) if is_customer else None

    if request.method == 'POST':
        if not is_customer:
            messages.error(request, 'Only customer accounts can buy products.')
            return redirect('manage_orders' if request.user.role == 'admin' else 'home')

        if form and form.is_valid():
            checkout_data = {
                'product_id': product.pk,
                'quantity': form.cleaned_data['quantity'],
                'selected_color': form.cleaned_data['selected_color'],
                'selected_size': form.cleaned_data['selected_size'],
            }
            request.session[checkout_session_key(product.pk)] = checkout_data
            request.session.modified = True
            return redirect('payment', pk=product.pk)

    context = {
        'product': product,
        'form': form,
        'admin_view': request.user.role == 'admin',
    }
    return render(request, 'inventory/product_detail.html', context)


def payment_view(request, pk):
    product = get_object_or_404(Product.objects.select_related('category'), pk=pk)
    next_url = reverse('payment', args=[product.pk])
    redirect_response = require_customer_access(request, next_url)
    if redirect_response:
        return redirect_response

    session_key = checkout_session_key(product.pk)

    if request.method == 'POST' and 'payment_method' not in request.POST:
        purchase_form = PurchaseForm(request.POST, product=product)
        if purchase_form.is_valid():
            request.session[session_key] = {
                'product_id': product.pk,
                'quantity': purchase_form.cleaned_data['quantity'],
                'selected_color': purchase_form.cleaned_data['selected_color'],
                'selected_size': purchase_form.cleaned_data['selected_size'],
            }
            request.session.modified = True
            return redirect('payment', pk=product.pk)

        return render(
            request,
            'inventory/product_detail.html',
            {
                'product': product,
                'form': purchase_form,
                'admin_view': False,
            },
        )

    checkout_data = request.session.get(session_key)
    if not checkout_data:
        messages.error(request, 'Please choose your quantity, color, and size first.')
        return redirect('product_detail', pk=product.pk)

    if checkout_data.get('product_id') != product.pk:
        messages.error(request, 'Your checkout session does not match this product.')
        return redirect('product_detail', pk=product.pk)

    form = PaymentForm(request.POST or None, initial={'payment_method': 'cash'})
    order_preview = {
        'product': product,
        'quantity': checkout_data['quantity'],
        'selected_color': checkout_data['selected_color'],
        'selected_size': checkout_data['selected_size'],
        'total_price': Decimal(checkout_data['quantity']) * product.price,
    }

    if request.method == 'POST' and 'payment_method' in request.POST and form.is_valid():
        with transaction.atomic():
            locked_product = Product.objects.select_for_update().get(pk=product.pk)
            quantity = int(checkout_data['quantity'])
            if quantity > locked_product.stock:
                messages.error(request, 'Not enough stock available for this order anymore.')
                return redirect('product_detail', pk=product.pk)

            order = Order.objects.create(
                customer=request.user,
                product=locked_product,
                quantity=quantity,
                selected_color=checkout_data['selected_color'],
                selected_size=checkout_data['selected_size'],
                payment_method=form.cleaned_data['payment_method'],
            )
            locked_product.stock -= quantity
            locked_product.save(update_fields=['stock'])

        request.session.pop(session_key, None)
        request.session.modified = True
        messages.success(request, 'Your order has been confirmed successfully.')
        return redirect('order_success', pk=order.pk)

    return render(
        request,
        'inventory/payment.html',
        {
            'product': product,
            'form': form,
            'order_preview': order_preview,
        },
    )


def order_success(request, pk):
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to view your order summary.')
        return redirect(login_redirect_for(reverse('order_success', args=[pk])))

    lookup = {'pk': pk}
    if request.user.role == 'customer':
        lookup['customer'] = request.user

    order = get_object_or_404(
        Order.objects.select_related('product', 'customer', 'product__category'),
        **lookup,
    )
    return render(request, 'inventory/order_success.html', {'order': order})


def my_orders(request):
    if not request.user.is_authenticated:
        messages.error(request, 'Please log in to view your orders.')
        return redirect(login_redirect_for(reverse('my_orders')))

    if request.user.role == 'admin':
        messages.info(request, 'Admin accounts use Order Records instead of My Orders.')
        return redirect('manage_orders')

    orders = Order.objects.select_related('product', 'product__category').filter(customer=request.user)
    return render(request, 'inventory/my_orders.html', {'orders': orders})


class ManageProductsView(AdminRequiredMixin, ListView):
    template_name = 'inventory/manage_products.html'
    model = Product
    context_object_name = 'products'

    def get_queryset(self):
        return Product.objects.select_related('category').all()


class ProductImageFormMixin:
    def handle_product_image(self, form, product):
        if form.cleaned_data.get('remove_existing_image'):
            delete_product_image(product)

        uploaded_image = form.cleaned_data.get('image_file')
        if uploaded_image:
            delete_product_image(product)
            image_url, image_pathname = upload_product_image(uploaded_image, product.name)
            product.image_blob_url = image_url
            product.image_blob_pathname = image_pathname
            product.image = None

    def form_invalid_with_image_error(self, form, error_text):
        form.add_error('image_file', error_text)
        return self.form_invalid(form)


class ProductCreateView(ProductImageFormMixin, AdminRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_url = reverse_lazy('manage_products')

    def form_valid(self, form):
        try:
            self.object = form.save(commit=False)
            self.handle_product_image(form, self.object)
            self.object.save()
        except ProductImageUploadError as exc:
            return self.form_invalid_with_image_error(form, str(exc))

        messages.success(self.request, 'Product created successfully.')
        return redirect(self.get_success_url())


class ProductUpdateView(ProductImageFormMixin, AdminRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'inventory/product_form.html'
    success_url = reverse_lazy('manage_products')

    def form_valid(self, form):
        try:
            self.object = form.save(commit=False)
            self.handle_product_image(form, self.object)
            self.object.save()
        except ProductImageUploadError as exc:
            return self.form_invalid_with_image_error(form, str(exc))

        messages.success(self.request, 'Product updated successfully.')
        return redirect(self.get_success_url())


class ProductDeleteView(AdminRequiredMixin, DeleteView):
    model = Product
    template_name = 'inventory/product_confirm_delete.html'
    success_url = reverse_lazy('manage_products')

    def form_valid(self, form):
        delete_product_image(self.object)
        messages.success(self.request, 'Product deleted successfully.')
        return super().form_valid(form)
