from django import forms
from django.contrib.auth import get_user_model

from .models import Category, Order, Product

User = get_user_model()


class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Enter your email'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Enter your password'})
    )


class SignUpForm(forms.ModelForm):
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Create password'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirm password'})
    )

    class Meta:
        model = User
        fields = ['full_name', 'email']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Enter your full name'}),
            'email': forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'Enter your email'}),
        }

    def clean_email(self):
        email = self.cleaned_data['email'].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('This email is already registered.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            self.add_error('password2', 'Passwords do not match.')

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'customer'
        user.username = None
        user.set_password(self.cleaned_data['password1'])
        if commit:
            user.save()
        return user


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Example: Beauty'}),
        }


class ProductForm(forms.ModelForm):
    new_category = forms.CharField(
        required=False,
        label='New Category',
        widget=forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Type a new category if not in list'})
    )
    image_file = forms.ImageField(
        required=False,
        label='Image',
        widget=forms.ClearableFileInput(attrs={'class': 'form-input', 'accept': 'image/*'}),
        help_text='Upload a product image. On Vercel, this will be saved to Blob storage.',
    )
    remove_existing_image = forms.BooleanField(
        required=False,
        label='Remove current image',
    )

    class Meta:
        model = Product
        fields = ['name', 'category', 'new_category', 'stock', 'price', 'available_colors', 'available_sizes', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'category': forms.Select(attrs={'class': 'form-input'}),
            'stock': forms.NumberInput(attrs={'class': 'form-input', 'min': 0}),
            'price': forms.NumberInput(attrs={'class': 'form-input', 'min': 0, 'step': '0.01'}),
            'available_colors': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Black, White, Blue'}),
            'available_sizes': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'S, M, L or leave blank'}),
            'description': forms.Textarea(attrs={'class': 'form-input', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].required = False
        self.fields['category'].queryset = Category.objects.order_by('name')
        self.fields['category'].empty_label = 'Select category'

        if self.instance and self.instance.pk:
            self.fields['new_category'].help_text = 'Optional. Only use this if you want to create and assign a brand new category.'
        else:
            self.fields['new_category'].help_text = 'Optional. Use this if your category is not in the list.'

        if not self.instance or not self.instance.pk or not self.instance.display_image_url:
            self.fields['remove_existing_image'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        category = cleaned_data.get('category')
        new_category = (cleaned_data.get('new_category') or '').strip()

        if not category and not new_category:
            raise forms.ValidationError('Please select a category or type a new category.')

        return cleaned_data


class PurchaseForm(forms.Form):
    quantity = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-input', 'min': 1})
    )
    selected_color = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-input'}))
    selected_size = forms.ChoiceField(widget=forms.Select(attrs={'class': 'form-input'}))

    def __init__(self, *args, product=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.product = product
        colors = [('None', 'None')]
        sizes = [('None', 'None')]

        if product:
            colors.extend((color, color) for color in product.colors_list)
            sizes.extend((size, size) for size in product.sizes_list)
            self.fields['quantity'].widget.attrs['max'] = product.stock

        self.fields['selected_color'].choices = colors
        self.fields['selected_size'].choices = sizes

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if self.product and quantity > self.product.stock:
            raise forms.ValidationError('Quantity cannot be greater than current stock.')
        return quantity


class PaymentForm(forms.Form):
    payment_method = forms.ChoiceField(
        choices=Order.PAYMENT_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'payment-choice'})
    )
