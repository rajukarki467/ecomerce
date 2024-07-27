from audioop import avg, reverse
import json
import logging
import math
from urllib.parse import unquote_plus
import numpy as np
import requests
import xml.etree.ElementTree as ET
from uuid import uuid4
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Q, FloatField, Value as V, Count
from django.db.models.functions import Coalesce
from django.http import Http404, HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views import View
from sklearn.feature_extraction.text import TfidfVectorizer
from .forms import *
from .models import *
from .recommend import *
from .models import OtpToken  # If you need to import OtpToken specifically
from .token import user_tokenizer_generate  # Make sure this is used in your code
from django.views.generic import View, TemplateView, DetailView, ListView, CreateView
from django.db.models import Avg
# Ensure logger is defined or imported correctly if needed
from venv import logger


def check_stock(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if product.quantity == 0:
        product.stock_status = "Out of Stock"
    elif product.quantity < 30:
        product.stock_status = "Limited Stock"
    else:
        product.stock_status = "In Stock"

    product.save()

    return JsonResponse({'message': product.stock_status, 'in_stock': product.quantity > 0})

def login_view(request):
   if request.method == 'POST':
      username = request.POST['username']
      password = request.POST['password']

      user = authenticate(request, username=username, password=password)
      if user is not None: 
        login(request, user)
        # seller = Seller.objects.get(user=user)
        # admin = Admin.objects.get(user=user)
        if Seller.objects.filter(user=user).exists():
            return redirect('sellerhome')
        elif Admin.objects.filter(user=user).exists():
            return redirect('adminhome')
        return redirect('home')
   
   form = LoginForm()
   return render(request, 'app/login.html', {'form':form})
   

def recommendations_view(request):
    totalitems = 0
    recommended_products = combined_recommendations(request.user) if request.user.is_authenticated else []

    if request.user.is_authenticated:
        for i in Cart.objects.filter(user=request.user):
            totalitems += i.quantity

    context = {
        'recommended_products': recommended_products,
        'totalitem': totalitems,
    }
    return render(request, 'app/recommendations.html', context)


class ProductView(View):
    def get(self, request):
        totalitems = 0
        recommended_products = combined_recommendations(request.user) if request.user.is_authenticated else []
        latestproduct = LatestProduct.get_latest_products()[:4]

        products = Product.objects.filter(quantity__gt=0).order_by("-id")
        
        paginator = Paginator(products, 8)
        page_number = request.GET.get('page')
        product_list = paginator.get_page(page_number)

        if request.user.is_authenticated:
            for i in Cart.objects.filter(user=request.user):
                totalitems += i.quantity

        context = {
            'recommended_products':recommended_products,
            'latestproduct': latestproduct,
            'product_list': product_list,
            'totalitem': totalitems,

        }
        return render(request, 'app/home.html', context)

def search_view(request):
    query = request.GET.get('q', '').lower()
    products = Product.objects.none()
    recommended_products = Product.objects.none()
    suggested_query = None
    
    if query:
        query_str = CATEGORY_MAP.get(query, query)  # Map to category code if it exists

        # Retrieve products matching the query and filter by quantity greater than 0
        products = Product.objects.annotate(
            category_match=Coalesce(Q(category__icontains=query_str), V(0), output_field=FloatField()),
            brand_match=Coalesce(Q(brand__icontains=query_str), V(0), output_field=FloatField()),
            title_match=Coalesce(Q(title__icontains=query_str), V(0), output_field=FloatField()),
            description_match=Coalesce(Q(description__icontains=query_str), V(0), output_field=FloatField()),
            relevance=(
                V(0.7) * Coalesce(Q(category__icontains=query_str), V(0), output_field=FloatField()) +
                V(0.18) * Coalesce(Q(brand__icontains=query_str), V(0), output_field=FloatField()) +
                V(0.1) * Coalesce(Q(title__icontains=query_str), V(0), output_field=FloatField()) +
                V(0.02) * Coalesce(Q(description__icontains=query_str), V(0), output_field=FloatField())
            )
        ).filter(
            Q(category__icontains=query_str) |
            Q(brand__icontains=query_str) |
            Q(title__icontains=query_str) |
            Q(description__icontains=query_str),
            quantity__gt=0  # Apply the filter for quantity greater than 0
        ).order_by('-relevance', '-id')
        
        # Save search history
        if request.user.is_authenticated:
            SearchHistory.objects.create(user=request.user, query=query)
            recommended_products = get_recommended_products(request.user)[:8]
    
    product_ids = request.COOKIES.get('product_ids', '')
    product_count_in_cart = len(set(product_ids.split('|'))) if product_ids else 0

    word = "Searched Result:"

    context = {
        'products': products,
        'word': word,
        'product_count_in_cart': product_count_in_cart,
        'query': query,
        'recommended_products': recommended_products,
    }

    return render(request, 'app/searchs.html', context)

class ProductDetailView(View):
    def get(self, request, pk):
        try:
            item_already_in_cart = False
            totalitems = 0
            rating_exists = False
            product = Product.objects.get(id=pk)
            related_product = Product.objects.exclude(id=product.pk).filter(category=product.category)[:8]
            
            # Calculate average rating for the product
            average_rating = Rating.objects.filter(product=product).aggregate(Avg('rating'))['rating__avg']
            average_rating_int = round(average_rating) if average_rating is not None else 0
            
            # Update average rating for the product (optional, depending on your use case)
            product.average_rating = average_rating_int
            product.save()
            
            ratings = Rating.objects.filter(product=product)
            total_ratings = len(ratings)
            
            all_ratings = Rating.objects.filter(product=product)
            
            if request.user.is_authenticated:
                totalitems = sum(item.quantity for item in Cart.objects.filter(user=request.user))
                item_already_in_cart = Cart.objects.filter(Q(product=product.id) & Q(user=request.user)).exists()
                rating_exists = Rating.objects.filter(user=request.user, product=product).first()
                
        except Product.DoesNotExist:
            raise Http404("Product does not exist")
        
        return render(request, 'app/productdetail.html', {
            'product': product,
            'item_already_in_cart': item_already_in_cart,
            'totalitem': totalitems,
            'related_product': related_product,
            'average_rating': average_rating_int,
            'all_ratings': all_ratings,
            'rating_exists': rating_exists,
        })

    def post(self, request, pk):
        if request.method == 'POST' and request.user.is_authenticated:
            product = get_object_or_404(Product, id=pk)
            totalitems = sum(item.quantity for item in Cart.objects.filter(user=request.user))
            item_already_in_cart = Cart.objects.filter(Q(product=product.id) & Q(user=request.user)).exists()
            
            rating_value_str = request.POST.get('rating')
            review_text = request.POST.get('review')
            
            if rating_value_str and review_text:
                try:
                    rating_value = int(rating_value_str)
                    
                    existing_rating = Rating.objects.filter(user=request.user, product=product).first()
                    if existing_rating:
                        existing_rating.rating = rating_value
                        existing_rating.review = review_text
                        existing_rating.save()
                        messages.success(request, 'Your rating and review have been updated!')
                    else:
                        Rating.objects.create(user=request.user, product=product, rating=rating_value, review=review_text)
                        messages.success(request, 'Thank you for your rating and review!')
                    
                    return redirect('product-detail', pk=pk)
                except ValueError:
                    messages.error(request, 'Invalid rating value. Please select a valid rating.')
            else:
                messages.error(request, 'Please provide both a rating and a review.')

        elif not request.user.is_authenticated:
            messages.error(request, 'You need to be logged in to submit a rating and review.')

        return redirect('product-detail', pk=pk)

# cart views

# Utility functions
def calculate_cart_totals(user, cart=None):
    if cart is None:
        cart = Cart.objects.filter(user=user)
    amount = sum(p.quantity * p.product.discounted_price for p in cart)
    total_amount = amount + 70.0  # Shipping amount
    total_items = sum(p.quantity for p in cart)
    return amount, total_amount, total_items



def calculate_total_items(user):
    return sum(item.quantity for item in Cart.objects.filter(user=user))

def apply_filters(queryset, request):
    brand = request.GET.get('brand')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')

    if brand:
        queryset = queryset.filter(brand__in=brand.split(','))
    if min_price:
        queryset = queryset.filter(discounted_price__gte=min_price)
    if max_price:
        queryset = queryset.filter(discounted_price__lte=max_price)

    return queryset

def product_list_view(request, category, context_name, template_name):
    products = Product.objects.filter(category=category, quantity__gt=0)
    products = apply_filters(products, request)
    total_items = calculate_total_items(request.user) if request.user.is_authenticated else 0
    context = {context_name: products, 'totalitem': total_items}
    return render(request, template_name, context)

# Views
@login_required
def add_to_cart(request):
    product = get_object_or_404(Product, id=request.GET.get('prod_id'))
    Cart.objects.create(user=request.user, product=product)
    return redirect('/cart')

def get_product_status(product, cart_quantity=0):
    remaining_quantity = product.quantity - cart_quantity
    if remaining_quantity == 0:
        return "This product is out of stock.", 'error'
    elif remaining_quantity < 30:
        return "Limited stock available.", 'warning'
    else:
        return "Product in stock.", 'success'

@login_required
def show_cart(request):
    cart = Cart.objects.filter(user=request.user).select_related('product')
    amount, total_amount, total_items = calculate_cart_totals(request.user, cart)
    
    # Add product status for each cart item
    cart_status = []
    for item in cart:
        status_message, status_type = get_product_status(item.product, item.quantity)
        cart_status.append({
            'item': item,
            'status_message': status_message,
            'status_type': status_type
        })
    
    template = 'app/addtocart.html' if cart.exists() else 'app/empty.html'
    return render(request, template, {
        'cart_status': cart_status,
        'totalamount': total_amount,
        'amount': amount,
        'totalitem': total_items
    })

@login_required
def update_cart(request, increment=True):
    if request.method == 'GET':
        cart_item = get_object_or_404(Cart, Q(product=request.GET['prod_id']) & Q(user=request.user))
        product = cart_item.product

        if increment:
            if cart_item.quantity < product.quantity:
                cart_item.quantity += 1
        else:
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
        
        cart_item.save()

        # Recalculate product status after updating the cart
        status_message, status_type = get_product_status(product, cart_item.quantity)

        amount, total_amount, total_items = calculate_cart_totals(request.user)
        
        data = {
            'quantity': cart_item.quantity,
            'amount': amount,
            'totalamount': total_amount,
            'totalitem': total_items,
            'status_message': status_message,
            'status_type': status_type,
            'product_id': product.id
        }
        return JsonResponse(data)

@login_required
def plus_cart(request):
    return update_cart(request, increment=True)

@login_required
def minus_cart(request):
    return update_cart(request, increment=False)

@login_required
def remove_cart(request):
    if request.method == 'GET':
        cart_item = get_object_or_404(Cart, Q(product=request.GET['prod_id']) & Q(user=request.user))
        cart_item.delete()
        amount, total_amount, total_items = calculate_cart_totals(request.user)
        data = {'amount': amount, 'totalamount': total_amount, 'totalitem': total_items}
        return JsonResponse(data)

@login_required
def buy_now(request):
    product = get_object_or_404(Product, id=request.GET.get('prod_id'))
    total_amount = product.discounted_price + 70.0  # Shipping amount
    addresses = Customer.objects.filter(user=request.user)
    return render(request, 'app/buynow.html', {'add': addresses, 'totalamount': total_amount, 'product': product, 'totalitem': 1})

class CategoryView(View):
    def get(self, request):
        categories = {
            'mansclothes': Product.objects.filter(category='M', quantity__gt=0),
            'womansclothes': Product.objects.filter(category='W', quantity__gt=0),
            'shoes': Product.objects.filter(category='S', quantity__gt=0),
            'cosmeticproduct': Product.objects.filter(category='C', quantity__gt=0)
        }
        total_items = calculate_total_items(request.user) if request.user.is_authenticated else 0
        categories['totalitem'] = total_items
        return render(request, 'app/category.html', categories)

@login_required
def shoes(request):
    return product_list_view(request, 'S', 'shoes', 'app/shoes.html')

@login_required
def cosmetic(request):
    return product_list_view(request, 'C', 'cosmetic', 'app/cosmetic.html')

@login_required
def mancloth(request):
    return product_list_view(request, 'M', 'mancloth', 'app/mancloth.html')

@login_required
def womancloth(request):
    return product_list_view(request, 'W', 'womancloth', 'app/womancloth.html')

@login_required
def checkout(request):
    user = request.user
    cart_items = Cart.objects.filter(user=user)
    amount, total_amount, total_items = calculate_cart_totals(user, cart_items)
    addresses = Customer.objects.filter(user=user)
    return render(request, 'app/checkout.html', {'add': addresses, 'totalamount': total_amount, 'cartitems': cart_items, 'totalitem': total_items})

@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    def get(self, request):
        customer = Customer.objects.filter(user=request.user)
        total_items = calculate_total_items(request.user)
        return render(request, 'app/profile.html', {'customer': customer, 'totalitems': total_items})

@login_required
def orders(request):
    orders = OrderPlaced.objects.filter(user=request.user, payment_completed=True)
    total_items = calculate_total_items(request.user)
    return render(request, 'app/orders.html', {'orderplaced': orders, 'totalitems': total_items})

# payment system

@method_decorator(login_required, name='dispatch')
class KhaltiRequestView(View):
    def get(self, request, *args, **kwargs):
        oid = request.GET.get('oid')
        order = get_object_or_404(OrderPlaced, id=oid.split('_')[1], user=request.user)
        context = {
            "order": order,
        }
        return render(request, "app/khaltirequest.html", context)

@method_decorator(login_required, name='dispatch')
class KhaltiVerifyView(View):
    def get(self, request, *args, **kwargs):
        token = request.GET.get("token")
        oid = request.GET.get("oid")
        user = request.user

        if not all([token, oid]):
            return HttpResponse("Invalid request parameters.", status=400)

        total = 0
        shipping_cost = 70
        order_ids_str = oid.split('_')[1]
        order_ids = [int(order_id) for order_id in order_ids_str.split(',')]

        orders = OrderPlaced.objects.filter(id__in=order_ids, user=user)
        for order in orders:
            total += order.total
        total += shipping_cost

        url = "https://khalti.com/api/v2/payment/verify/"
        payload = {
            "token": token,
            "amount": total * 100  # Khalti API expects amount in paisa
        }
        headers = {
            "Authorization": "Key test_secret_key_26defbc7620b48c0a4395c6948bd1967"
        }

        response = requests.post(url, data=payload, headers=headers)
        resp_dict = response.json()
        if resp_dict.get("idx"):
            success = True

            with transaction.atomic():
                for order in orders:
                    order.payment_completed = True
                    order.payment_method = "Khalti"
                    order.save()

                    # Decrease quantity from products
                    product = order.product
                    product.quantity -= order.quantity
                    product.save()
            
            # Clear cart items
            Cart.objects.filter(user=user).delete()
        else:
            success = False

        data = {
            "success": success
        }
        return JsonResponse(data)



@login_required
def payment_done(request):
    user = request.user
    cart = Cart.objects.filter(user=user)
    payment = request.GET.get('payment')
    order_ids = []

    with transaction.atomic():
        for c in cart:
            order = OrderPlaced(user=user, product=c.product, quantity=c.quantity, total=c.total_cost)
            order.save()
            order_ids.append(str(order.id))

        if payment == 'Cash':
            for order_id in order_ids:
                order = OrderPlaced.objects.get(id=order_id)
                order.payment_completed = True
                order.payment_method = "Cash on Delivery"
                order.save()

                product = order.product
                if product.quantity>=order.quantity:
                    product.quantity -= order.quantity
                    product.save()
                else:
                    messages.error(request, 'Cannot order it! Product out of stock')

                 

        elif payment == 'e-sewa':
            oid = f"esewa_{','.join(order_ids)}"
            return redirect(f'/esewa-request/?oid={oid}')

        elif payment == 'khalti':
            oid = f"khalti_{','.join(order_ids)}"
            return redirect(f'/khalti-request/?oid={oid}')

        cart.delete()

    return redirect("orders")



@method_decorator(login_required, name='dispatch')
class EsewaRequestView(View):
    def get(self, request, *args, **kwargs):
        user = request.user
        uid = str(uuid4())  # Generate a unique ID
        total = 0
        cart_items = Cart.objects.filter(user=user)
        shipping_cost = 70
        
        for item in cart_items:
            total += item.quantity * item.product.discounted_price

        oid = request.GET.get('oid')
        total = shipping_cost + total 
        return render(request, 'app/esewarequest.html', {'uid': uid, 'total': total, 'oid': oid})


logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class EsewaVerifyView(View):
    def get(self, request, *args, **kwargs):
        oid = request.GET.get("oid")
        amt = request.GET.get("amt")
        refId = request.GET.get("refId")

        if not all([oid, amt, refId]):
            return HttpResponse("Invalid request parameters.", status=400)

        url = "https://uat.esewa.com.np/epay/transrec"
        data = {
            'amt': amt,
            'scd': 'EPAYTEST',
            'rid': refId,
            'pid': oid,
        }

        try:
            response = requests.post(url, data)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Network error: {e}")
            return HttpResponse("Network error occurred.", status=500)

        try:
            root = ET.fromstring(response.content)
            status = root.find(".//response_code").text.strip()
        except (ET.ParseError, AttributeError) as e:
            logger.error(f"Error parsing response: {e}")
            return HttpResponse("Error processing payment response.", status=500)

        if status == "Success":
            try:
                # Split oid to get order ids for each product
                order_ids_str = oid.split("_")[2]
                order_ids_str_decoded = unquote_plus(order_ids_str)
                order_ids_list = order_ids_str_decoded.split(",")
                order_ids = [int(order_id) for order_id in order_ids_list]

                with transaction.atomic():
                    for order_id in order_ids:
                        order_obj = OrderPlaced.objects.get(id=order_id)

                        if not order_obj.payment_completed:
                            order_obj.payment_completed = True
                            order_obj.payment_method = 'e-sewa'  # Set the payment method
                            order_obj.save()

                            # Decrease quantity from product
                            product = order_obj.product
                            product.quantity -= order_obj.quantity
                            product.save()

                    # Delete cart items for the user
                    Cart.objects.filter(user=request.user).delete()

                return redirect("orders")  # Redirect to the orders page after successful payment
            except OrderPlaced.DoesNotExist as e:
                logger.error(f"Order not found: {e}")
                return HttpResponse("Order not found.", status=404)

        else:
            # Payment failed, delete the temporary orders
            order_ids_str = oid.split("_")[2]
            order_ids_str_decoded = unquote_plus(order_ids_str)
            order_ids_list = order_ids_str_decoded.split(",")
            order_ids = [int(order_id) for order_id in order_ids_list]
            for order_id in order_ids:
                try:
                    order_obj = OrderPlaced.objects.get(id=order_id)
                    order_obj.delete()
                except OrderPlaced.DoesNotExist:
                    pass  # Handle case if order is already deleted

            return redirect("orders")  # Redirect back to the orders page


from django.db import transaction
class CustomerRegistrationView(View):
    def get(self, request):
        form = CustomerRegistrationForm()
        return render(request, 'app/customerregistration.html', {'form': form})

    def post(self, request):
        form = CustomerRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            with transaction.atomic():
                user = form.save(commit=False)
                user.is_active = False
                user.save()

                # Create the Customer instance
                phone = form.cleaned_data.get('phone')
                image = form.cleaned_data.get('image')
                locality = form.cleaned_data.get('locality')
                city = form.cleaned_data.get('city')
                state = form.cleaned_data.get('state')
                Customer.objects.create(
                    user=user,
                    locality=locality,
                    city=city,
                    state=state,
                    phone=phone,
                    image=image
                )

                messages.success(request, "Account created successfully! An OTP was sent to your Email")
                return redirect("verify-email", username=user.username)
        return render(request, 'app/customerregistration.html', {'form': form})

def verify_email(request, username):
    user = User.objects.get(username=username)
    # customer = Customer.objects.get(user=user)
    user_otp = OtpToken.objects.filter(user=user).last()
    
    
    if request.method == 'POST':
        # valid token
        if user_otp.otp_code == request.POST['otp_code']:
            
            # checking for expired token
            if user_otp.otp_expires_at > timezone.now():
                user.is_active=True
                user.save()
                # customer.save()
                messages.success(request, "Account activated successfully!! You can Login.")
                return redirect("login_view")
            
            # expired token
            else:
                messages.warning(request, "The OTP has expired, get a new OTP!")
                return redirect("verify-email", username=user.username)
        
        
        # invalid otp code
        else:
            messages.warning(request, "Invalid OTP entered, enter a valid OTP!")
            return redirect("verify-email", username=user.username)
        
    context = {}
    return render(request, "app/verify_token.html", context)




def resend_otp(request):
    if request.method == 'POST':
        user_email = request.POST["otp_email"]
        
        if User.objects.filter(email=user_email).exists():
            user = User.objects.get(email=user_email)
            otp = OtpToken.objects.create(user=user, otp_expires_at=timezone.now() + timezone.timedelta(minutes=5))
            # email variables
            subject="Email Verification"
            message = f"""
                                Hi {user.username}, here is your OTP {otp.otp_code} 
                                it expires in 5 minute, use the url below to redirect back to the website
                                http://127.0.0.1:8000/verify-email/{user.username}
                                
                                """
            sender = "rajukarki467@gmail.com"
            receiver = [user.email ]
            # send email
            send_mail(
                    subject,
                    message,
                    sender,
                    receiver,
                    fail_silently=False,
                )
            messages.success(request, "A new OTP has been sent to your email-address")
            return redirect("verify-email", username=user.username)

        else:
            messages.warning(request, "This email dosen't exist in the database")
            return redirect("resend-otp")
    
    context = {}
    return render(request, "app/resend_otp.html", context)

@login_required
def seller_dashboard( request):
    seller = Seller.objects.get(user=request.user)
    product = Product.objects.filter(seller=request.user)
    context = {
        'seller':seller,
        'product':product
    }
    return render(request, 'app/seller/seller_dashboard.html',context)

@login_required
def sellerprofile(request):
    seller = Seller.objects.get(user=request.user)
    context =  {'seller':seller, 'user':request.user}
    return render(request, 'app/seller/sellerprofile.html',context=context)

@login_required
def sellerhome(request):
    seller = Seller.objects.get(user=request.user)
    products = Product.objects.filter(seller=request.user)
    context = {
        'products':products,
        'user':request.user,
        'seller':seller
    }
    return render(request, 'app/seller/sellerhome.html', context)

@login_required
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.seller = request.user  # Set the seller attribute of the product
            product.save()  # Save the product instance
            messages.success(request, 'Product added successfully!')
            return redirect('sellerdashboard')  # Redirect to a seller dashboard or another page
    else:
        form = ProductForm()
    return render(request, 'app/seller/add_product.html', {'form': form})




def aboutus(request):
   return render(request,'app/about.html')

def contactus(request):
   return render(request,'app/contactus.html')

def chat(request):
   return render(request,'app/chat.html')


class AdminRequiredMixin:
    @method_decorator(login_required(login_url='/admin-login/'))
    def dispatch(self, request, *args, **kwargs):
        if not Admin.objects.filter(user=request.user).exists():
            return redirect("/login/")
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['admin'] = Admin.objects.get(user=self.request.user)
        return context

@login_required
def admin_dashboard(request):
    admin = get_object_or_404(Admin, user=request.user)
    products = Product.objects.filter(admin=admin)  # Assuming 'admin' is the related field in Product

    context = {
        'admin': admin,
        'products': products
    }
    return render(request, 'app/adminpages/admin_dashboard.html', context)

@method_decorator(login_required, name='dispatch')
class AdminHomeView(AdminRequiredMixin, TemplateView):
    template_name = "app/adminpages/adminhome.html"

    def get_context_data(self, **kwargs):
      pendingorders=OrderPlaced.objects.filter(status="Pending").order_by("-id")
      admin = Admin.objects.get(user=self.request.user)

      paginator = Paginator(pendingorders, 20)
      page_number = self.request.GET.get('page')
      print(page_number)
      product_list = paginator.get_page(page_number)
      context = super().get_context_data(**kwargs)
      context= {
         "pendingorders" : product_list,
         'admin':admin
         }

      return context

@method_decorator(login_required, name='dispatch')
class DeliveredOrderView(AdminRequiredMixin, TemplateView):
    template_name = "app/adminpages/deliveredorder.html"

    def get_context_data(self, **kwargs):
      pendingorders=OrderPlaced.objects.filter(status="Delivered").order_by("-id")
      admin = Admin.objects.get(user=self.request.user)

      paginator = Paginator(pendingorders, 20)
      page_number = self.request.GET.get('page')
      print(page_number)
      product_list = paginator.get_page(page_number)
      context = super().get_context_data(**kwargs)
      context= {
         "pendingorders" : product_list,
         'admin':admin
         }

      return context
    
@method_decorator(login_required, name='dispatch')
class CancelOrderView(AdminRequiredMixin, TemplateView):
    template_name = "app/adminpages/cancelorder.html"

    def get_context_data(self, **kwargs):
      pendingorders=OrderPlaced.objects.filter(status="Cancel").order_by("-id")
      admin = Admin.objects.get(user=self.request.user)

      paginator = Paginator(pendingorders, 20)
      page_number = self.request.GET.get('page')
      print(page_number)
      product_list = paginator.get_page(page_number)
      context = super().get_context_data(**kwargs)
      context= {
         "pendingorders" : product_list,
         'admin':admin
         }

      return context
@method_decorator(login_required, name='dispatch')
class AdminOrderDetailView(AdminRequiredMixin, DetailView):
    template_name = "app/adminpages/adminorderdetail.html"
    model = OrderPlaced
    context_object_name = "ord_obj"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["allstatus"]= ORDER_STATUS 
        return context

@method_decorator(login_required, name='dispatch')
class AdminOrderListView(AdminRequiredMixin, ListView):
    template_name = "app/adminpages/adminorderlist.html"
    queryset = OrderPlaced.objects.all().order_by("-id")
    context_object_name = "order"
    def get_context_data(self, **kwargs):
        admin= Admin.objects.get(user=self.request.user)

        order = OrderPlaced.objects.all().order_by("-id")
        paginator = Paginator(order, 25)
        page_number = self.request.GET.get('page')
        print(page_number)
        product_list = paginator.get_page(page_number)
        context = super().get_context_data(**kwargs)
        context= {
            'order' : product_list,
            'admin':admin
            }
        return context
    
@method_decorator(login_required, name='dispatch')
class AdminOrderStatusChangeView(AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        order_id = self.kwargs["pk"]
        order_obj = OrderPlaced.objects.get(id=order_id)
        new_status = request.POST.get("status")
        order_obj.order_status = new_status
        order_obj.save()
        return redirect(reverse_lazy("adminorderdetail", kwargs={"pk": order_id}))

@method_decorator(login_required, name='dispatch')
class AdminProductListView(AdminRequiredMixin, ListView):
    template_name = "app/adminpages/adminproductlist.html"
    queryset = Product.objects.all().order_by("-id")
    context_object_name = "products"

    def get_context_data(self, **kwargs):
        products = Product.objects.all().order_by("-id")
        paginator = Paginator(products, 15)
        page_number = self.request.GET.get('page')
        print(page_number)
        product_list = paginator.get_page(page_number)
        context = super().get_context_data(**kwargs)
        context= {
            'products' : product_list,
            }
        return context
    
@method_decorator(login_required, name='dispatch')
class AdminCustomerListView(AdminRequiredMixin, ListView):
    template_name = "app/adminpages/admincustomerlist.html"
    queryset = Customer.objects.all().order_by("-id")
    context_object_name = "products"

    def get_context_data(self, **kwargs):
        product = Customer.objects.all().order_by("-id")
        paginator = Paginator(product, 15)
        page_number = self.request.GET.get('page')
        print(page_number)
        product_list = paginator.get_page(page_number)
        context = super().get_context_data(**kwargs)
        context= {
            'products' : product_list,
            }
        return context

@method_decorator(login_required, name='dispatch')
class AdminSellerListView(AdminRequiredMixin, ListView):
    template_name = "app/adminpages/adminsellerlist.html"
    queryset = Seller.objects.all().order_by("-id")
    context_object_name = "products"

    def get_context_data(self, **kwargs):
        products = Seller.objects.all().order_by("-id")
        paginator = Paginator(products, 15)
        page_number = self.request.GET.get('page')
        print(page_number)
        product_list = paginator.get_page(page_number)
        context = super().get_context_data(**kwargs)
        context= {
            'products' : product_list,
            }
        return context

@method_decorator(login_required, name='dispatch')
class AdminAdminListView(AdminRequiredMixin, ListView):
    template_name = "app/adminpages/adminadminlist.html"
    queryset = Admin.objects.all().order_by("-id")
    context_object_name = "products"

    def get_context_data(self, **kwargs):
        products = Admin.objects.all().order_by("-id")
        paginator = Paginator(products, 15)
        page_number = self.request.GET.get('page')
        print(page_number)
        product_list = paginator.get_page(page_number)
        context = super().get_context_data(**kwargs)
        context= {
            'products' : product_list,
            }
        return context            


@login_required
def admin_product_create(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            id = request.session.get('admin_id')
            product = form.save(commit=False)
            product.admin= Admin.objects.get(id= id) 
            product.save()
            messages.success(request, 'Product created successfully!')
            return redirect('adminproductlist')
    else:
        form = ProductForm()
    
    return render(request, 'app/adminpages/adminproductcreate.html', {'form': form})


@login_required
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    messages.success(request, 'Product deleted successfully!')
    return HttpResponseRedirect(reverse('adminproductlist'))


from django.http import JsonResponse
from .chatbot_model import get_response  # Import your function

def chatbot_response(request):
    query = request.GET.get('query', '')
    user_message = request.GET.get('query', '').lower()
    response  = get_response(user_message)  # Use the function to get response and products

    response, recommended_products = get_response(query)
    
    # Check if recommended_products is a QuerySet
    if hasattr(recommended_products, 'model'):
        products = [
            {
                'title': product.title,
                'price': product.discounted_price,
                'image_url': product.product_image.url,
                'product_url': product.get_absolute_url(),
                'stock_status': product.stock_status
            }
            for product in recommended_products
        ]
    else:
        # If not a QuerySet, fallback to empty list
        products = []
    
    return JsonResponse({'response': response, 'products': products})


from .chatbot_model import get_response  # Import the function


from django.shortcuts import render
from django.http import JsonResponse
from .models import Customer, OrderPlaced, Cart

def customer_info(request):
    user_id = request.user.id
    customer = Customer.objects.get(user_id=user_id)
    orders = OrderPlaced.objects.filter(user_id=user_id)
    cart_items = Cart.objects.filter(user_id=user_id)

    customer_data = {
        "name": customer.user.username,
        "locality": customer.locality,
        "city": customer.city,
        "state": customer.state,
        "phone": customer.phone,
    }

    order_data = []
    for order in orders:
        order_data.append({
            "product": order.product.title,
            "quantity": order.quantity,
            "total": order.total,
            "status": order.status,
            "ordered_date": order.ordered_date,
        })

    cart_data = []
    for item in cart_items:
        cart_data.append({
            "product": item.product.title,
            "quantity": item.quantity,
            "total_cost": item.total_cost,
        })

    return JsonResponse({
        "customer_info": customer_data,
        "orders": order_data,
        "cart_items": cart_data,
    })

