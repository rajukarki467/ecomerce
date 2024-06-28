from django import forms
from django.contrib.auth.forms import UserCreationForm , AuthenticationForm ,UsernameField ,PasswordChangeForm , PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django.utils.translation import gettext ,gettext_lazy as _
from django.contrib.auth import password_validation
from pydantic import ValidationError, validate_email
from .models import Customer, Product,Seller



class CustomerRegistrationForm(UserCreationForm):
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label='Confirm Password (again)', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    email = forms.CharField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
    phone = forms.CharField(required=True, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    image = forms.ImageField( widget=forms.FileInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        labels = {'email': 'Email'}
        widgets = {'username': forms.TextInput(attrs={'class': 'form-control'})}

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']  # Custom field, may need extra handling
        if commit:
            user.save()
            self.save_m2m()
        return user

# class SellerRegistrationForm(forms.ModelForm):
#     password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
#     password2 = forms.CharField(label='Confirm Password (again)', widget=forms.PasswordInput(attrs={'class': 'form-control'}))

#     class Meta:
#         model = Seller
#         fields = [ 'username','phone', 'address', 'image']
#         widgets = {
#             'phone': forms.NumberInput(attrs={'class': 'form-control'}),
#             'address': forms.TextInput(attrs={'class': 'form-control'}),
#             'image': forms.FileInput(attrs={'class': 'form-control'}),
#         }

#     def clean_password2(self):
#         password1 = self.cleaned_data.get('password1')
#         password2 = self.cleaned_data.get('password2')
#         if password1 and password2 and password1 != password2:
#             raise forms.ValidationError("Passwords don't match")
#         return password2

# class SellerRegistrationForm(UserCreationForm):
#     username= forms.TextInput(attrs={'class': 'form-control'})
#     password1 = forms.CharField(label='Password', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
#     password2 = forms.CharField(label='Confirm Password (again)', widget=forms.PasswordInput(attrs={'class': 'form-control'}))
#     email = forms.CharField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))
#     phone = forms.CharField(required=True, widget=forms.NumberInput(attrs={'class': 'form-control'}))
#     image = forms.ImageField( widget=forms.FileInput(attrs={'class': 'form-control'}))

#     class Meta:
#         model = User
#         fields = ['username',  'password1', 'password2']
#         labels = {'email': 'Email'}
#         widgets = {'username': forms.TextInput(attrs={'class': 'form-control'})}

#     def save(self, commit=True):
#         seller = super().save(commit=False)
#         seller.email = self.cleaned_data['email']
#         seller.phone = self.cleaned_data['phone']  # Custom field, may need extra handling
#         if commit:
#             seller.save()
#             self.save_m2m()
#         return seller
    

class LoginForm(AuthenticationForm):
    username = UsernameField(widget=forms.TextInput(attrs={'autofocus':True ,'class':'form-control'}))   
    password = forms.CharField(label=_("Password"), strip=False, widget=forms.PasswordInput(attrs={'autocomplete':'current-password' ,'class':'form-control'}))


# class SellerLoginForm(forms.Form):
#     email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
#     password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))

class MyPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(label=('Old Password'), strip=False ,widget=forms.PasswordInput(attrs={'autocomplete':'current-password','autofocus':True, 'class':'form-control'}))
    new_password1 = forms.CharField(label=_('New Password'), strip=False ,widget=forms.PasswordInput(attrs={'autocomplete':'new-password','class':'form-control'}),help_text=password_validation.password_validators_help_text_html())
    new_password2 = forms.CharField(label=('Confirm New Password'), strip=False ,widget=forms.PasswordInput(attrs={'autocomplete':'new-password', 'class':'form-control'}))

class MyPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(label=_("Email"), max_length=100, widget=forms.EmailInput(attrs={'autocomplete': 'email', 'class':'form-control'}))


class MySetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(label=_('New Password'), strip=False ,widget=forms.PasswordInput(attrs={'autocomplete':'new-password','class':'form-control'}),help_text=password_validation.password_validators_help_text_html())
    new_password2 = forms.CharField(label=('Confirm New Password'), strip=False ,widget=forms.PasswordInput(attrs={'autocomplete':'new-password', 'class':'form-control'}))
      

class CustomerProfileForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields =['name','locality','city','state']
        widgets={'name':forms.TextInput(attrs={'class':'form-control'}), 'locality':forms.TextInput(attrs={'class':'form-control'})
                 ,'city':forms.TextInput(attrs={'class':'form-control'}),'state':forms.Select(attrs={'class':'form-control'})}


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['title', 'selling_price', 'discounted_price', 'description', 'brand', 'category', 'product_image', 'quantity']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'discounted_price': forms.NumberInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'product_image': forms.FileInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
        }