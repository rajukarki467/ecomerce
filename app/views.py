from django.core.paginator import Paginator
from uuid import uuid4
from venv import logger
from django.shortcuts import get_object_or_404, render ,redirect
from django.views import View
import numpy as np
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import requests
from django.urls import reverse_lazy
from .models import *
from .forms import *
import xml.etree.ElementTree as ET
import logging
from django.contrib.auth import authenticate, login
from django.core.mail import send_mail
from .models import OtpToken
# for email varification 
from django.contrib.sites.shortcuts import get_current_site
from .token import user_tokenizer_generate
from django.template.loader import render_to_string
from django.utils.encoding import force_bytes,force_str
from django.utils.http import urlsafe_base64_decode,urlsafe_base64_encode



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
   

# recommendation views
def user_based_collaborative_filtering(user, num_recommendations=8):
    # Get all users except the target user
    other_users = User.objects.exclude(id=user.id)

    # Calculate user similarity using cosine similarity
    user_similarities = []
    for other_user in other_users:
        ratings_user = Rating.objects.filter(user=user)
        ratings_other_user = Rating.objects.filter(user=other_user)

        common_products = set(ratings_user.values_list('product_id', flat=True)) & set(ratings_other_user.values_list('product_id', flat=True))

        if common_products:
            user_ratings = []
            other_user_ratings = []

            for product_id in common_products:
                user_rating = ratings_user.get(product_id=product_id).rating
                other_user_rating = ratings_other_user.get(product_id=product_id).rating

                user_ratings.append(user_rating)
                other_user_ratings.append(other_user_rating)

            # Calculate cosine similarity manually
            similarity = np.dot(user_ratings, other_user_ratings) / (np.linalg.norm(user_ratings) * np.linalg.norm(other_user_ratings))
            user_similarities.append((other_user, similarity))

    # Sort similar users by similarity
    user_similarities.sort(key=lambda x: x[1], reverse=True)

    # Generate recommendations based on similar users' high-rated products
    recommended_products = set()

    for similar_user, similarity in user_similarities:
        similar_user_ratings = Rating.objects.filter(user=similar_user, rating__gte=4)

        for rating in similar_user_ratings:
            recommended_products.add(rating.product)

        if len(recommended_products) >= num_recommendations:
            break

    return list(recommended_products)[:num_recommendations]
    

def search_view(request):
    query = request.GET.get('q', '')
    products = Product.objects.filter(
        Q(category__icontains=query) |
        Q(brand__icontains=query) |
        Q(discounted_price__icontains=query)
    ) if query else Product.objects.none()

    product_ids = request.COOKIES.get('product_ids', '')
    product_count_in_cart = len(set(product_ids.split('|'))) if product_ids else 0

    word = "Searched Result:"

    context = {
        'products': products,
        'word': word,
        'product_count_in_cart': product_count_in_cart,
        'query': query,
    }

    return render(request, 'app/search.html', context)

class ProductView(View):
 def get(self,request):
  totalitems = 0
  recommended_products = []
  latestproduct = LatestProduct.get_latest_products()[:4]

  product = Product.objects.all().order_by("-id")
  paginator = Paginator(product, 8)
  page_number = self.request.GET.get('page')
  print(page_number)
  product_list = paginator.get_page(page_number)
  if request.user.is_authenticated:
   recommended_products = user_based_collaborative_filtering(request.user)
   print(recommended_products)
   
   for i in Cart.objects.filter(user=request.user):
    totalitems+=i.quantity
  return render(request ,'app/home.html',{'latestproduct': latestproduct,'product_list':product_list,'totalitem':totalitems,'recommended_products': recommended_products})

class ProductDetailView(View):
    def get(self, request, pk):
        try:
            item_already_in_cart = False
            totalitems = 0
            rating_exists = False
            product = Product.objects.get(id=pk)
            related_product = Product.objects.exclude(id=product.pk).filter(category=product.category)[:8]
            
            ratings = Rating.objects.filter(product=product)
            total_ratings = len(ratings)
            if total_ratings > 0:
                average_rating = sum(rating.rating for rating in ratings) / total_ratings
            else:
                average_rating = 0
            all_ratings = Rating.objects.filter(product=product)
            
            if request.user.is_authenticated:
                totalitems = sum(item.quantity for item in Cart.objects.filter(user=request.user))
                item_already_in_cart = Cart.objects.filter(Q(product=product.id) & Q(user=request.user)).exists()
                rating_exists = Rating.objects.filter(user=request.user, product=product).first()

        except Product.DoesNotExist:
            raise
        final_price = product.selling_price-product.discounted_price
        return render(request, 'app/productdetail.html', {
            'product': product,
            'final_price':final_price,
            'item_already_in_cart': item_already_in_cart,
            'totalitem': totalitems,
            'related_product': related_product,
            'average_rating': average_rating,
            'all_ratings': all_ratings,
            'rating_exists':rating_exists
        })

    def post(self, request, pk):
        if request.method == 'POST' and request.user.is_authenticated:
            product = get_object_or_404(Product, id=pk)
            totalitems = 0
            for item in Cart.objects.filter(user=request.user):
                totalitems += item.quantity
            item_already_in_cart = Cart.objects.filter(Q(product=product.id) & Q(user=request.user)).exists()
            
            rating_value_str = request.POST.get('rating')
            review_text = request.POST.get('review')
            
            if rating_value_str is not None and review_text is not None:
                try:
                    rating_value = int(rating_value_str)
                    
                    # Check if the user has already rated the product
                    existing_rating = Rating.objects.filter(user=request.user, product=product).first()
                    if existing_rating:
                        existing_rating.rating = rating_value
                        existing_rating.review = review_text
                        existing_rating.save()
                        messages.success(request, 'Your rating and review have been updated!')
                    else:
                        Rating.objects.create(user=request.user, product=product, rating=rating_value, review=review_text)
                        messages.success(request, 'Thank you for your rating and review!')
                    
                    return redirect('/product-detail/'+str(pk), pk=pk)
                except ValueError:
                    messages.error(request, 'Invalid rating value. Please select a valid rating.')
            else:
                messages.error(request, 'Please provide both a rating and a review.')

        elif request.method == 'POST' and not request.user.is_authenticated:
            messages.error(request, 'You need to be logged in to submit a rating and review.')

        return redirect('/product-detail/'+str(pk), pk=pk)
# cart views

@login_required
def add_to_cart(request):
 user = request.user 
 product_id=request.GET.get('prod_id')
#  product_id=request.POST['prod_id']

 product=Product.objects.get(id=product_id)
 Cart(user=user, product=product).save()
 return redirect('/cart')

@login_required
def show_cart(request):
  user = request.user
  cart = Cart.objects.filter(user=user)
  amount= 0.0 
  shipping_amount = 70.0
  total_amount = 0.0
  cart_product = [p for p in Cart.objects.all() if p.user == user]
  if cart_product:
   for p in cart_product:
    tempamount = (p.quantity * p.product.discounted_price)
    amount += tempamount
    totalamount = amount + shipping_amount
    totalitems = 0
    for i in Cart.objects.filter(user=request.user):
      totalitems+=i.quantity
   return render(request, 'app/addtocart.html',{'carts':cart, 'totalamount':totalamount,'amount':amount,'totalitem':totalitems})
  else:
   return render(request, 'app/empty.html')
 
@login_required
def plus_cart(request):
 if request.method == 'GET':
  prod_id= request.GET['prod_id']
  c = Cart.objects.get(Q(product =prod_id) & Q(user=request.user))
  product = Product.objects.get(id=prod_id)
  if c.quantity <product.quantity:
   c.quantity+=1
  c.save()
  amount= 0.0 
  shipping_amount = 70.0
  cart_product = [p for p in Cart.objects.all() if p.user ==request.user]
  for p in cart_product:
    tempamount = (p.quantity * p.product.discounted_price)
    amount += tempamount
  
  totalitems = 0
  for i in Cart.objects.filter(user=request.user):
    totalitems+=i.quantity

  data= {
    'quantity':c.quantity,
    'amount':amount,
    'totalamount':amount + shipping_amount,
    'totalitem':totalitems,
  }
  return JsonResponse(data)

@login_required 
def minus_cart(request):
 if request.method == 'GET':
  prod_id= request.GET['prod_id']
  c = Cart.objects.get(Q(product =prod_id) & Q(user=request.user))
  if c.quantity >1:
   c.quantity-=1
  c.save()
  amount= 0.0 
  shipping_amount = 70.0
  cart_product = [p for p in Cart.objects.all() if p.user ==request.user]
  for p in cart_product:
    tempamount = (p.quantity * p.product.discounted_price)
    amount += tempamount

  totalitems = 0
  for i in Cart.objects.filter(user=request.user):
   totalitems+=i.quantity  


  data= {
    'quantity':c.quantity,
    'amount':amount,
    'totalamount':amount + shipping_amount,
    'totalitem': totalitems
   }

  return JsonResponse(data)
 
@login_required
def remove_cart(request):
 if request.method == 'GET':
  prod_id= request.GET['prod_id']
  c = Cart.objects.get(Q(product =prod_id) & Q(user=request.user))
  c.delete()
  amount= 0.0 
  shipping_amount = 70.0
  cart_product = [p for p in Cart.objects.all() if p.user ==request.user]
  for p in cart_product:
    tempamount = (p.quantity * p.product.discounted_price)
    amount += tempamount

  totalitems = 0
  for i in Cart.objects.filter(user=request.user):
    totalitems+=i.quantity  

  data= {
    'amount':amount,
    'totalamount':amount + shipping_amount,
    'totalitem':totalitems,
   }
  return JsonResponse(data)
 
def buy_now(request):
 user = request.user 
 add = Customer.objects.filter(user=user)
 product_id=request.GET.get('prod_id')
 product=Product.objects.get(id=product_id)
 amount= 0.0 
 shipping_amount = 70.0
 totalamount=0.0
 amount =  product.discounted_price
 totalamount +=amount +shipping_amount
 totalitems=1
 return render(request, 'app/buynow.html',{'add':add,'totalamount':totalamount,'product':product,'totalitem':totalitems})



# category views

class category(View):
 def get(self,request):
    mansclothes = Product.objects.filter(category ='M')
    womansclothes = Product.objects.filter(category ='W')
    shoes = Product.objects.filter(category ='S')
    cosmeticproduct = Product.objects.filter(category ='C')
    totalitems = 0
    if request.user.is_authenticated:
     for i in Cart.objects.filter(user=request.user):
        totalitems+=i.quantity
    return render(request ,'app/category.html',{'mansclothes':mansclothes, 
                'womansclothes':womansclothes, 'shoes':shoes , 'cosmeticproduct':cosmeticproduct , 'totalitem':totalitems})
 

def shoes(request):
    shoes = Product.objects.filter(category='S')
    
    # Get filter parameters from request
    brand = request.GET.get('brand')
    price_range = request.GET.get('price')

    # Apply brand filter if provided
    if brand:
        brand_list = brand.split(',')
        shoes = shoes.filter(brand__in=brand_list)

    # Apply price range filter if provided
    if price_range == 'below':
        shoes = shoes.filter(discounted_price__lt=1000)
    elif price_range == 'above':
        shoes = shoes.filter(discounted_price__gt=1000)

    totalitems = 0
    if request.user.is_authenticated:
        for item in Cart.objects.filter(user=request.user):
            totalitems += item.quantity

    return render(request, 'app/shoes.html', {'shoes': shoes, 'totalitem': totalitems})


def cosmetic(request):
    cosmetic = Product.objects.filter(category='C')
    
    # Get filter parameters from request
    brand = request.GET.get('brand')
    price_range = request.GET.get('price')

    # Apply brand filter if provided
    if brand:
        brand_list = brand.split(',')
        cosmetic = cosmetic.filter(brand__in=brand_list)

    # Apply price range filter if provided
    if price_range == 'below':
        cosmetic = cosmetic.filter(discounted_price__lt=1000)
    elif price_range == 'above':
        cosmetic = cosmetic.filter(discounted_price__gt=1000)

    totalitems = 0
    if request.user.is_authenticated:
        for item in Cart.objects.filter(user=request.user):
            totalitems += item.quantity

    return render(request, 'app/cosmetic.html', {'cosmetic': cosmetic, 'totalitem': totalitems})


def mancloth(request):
    mancloth = Product.objects.filter(category='M')
    
    # Get filter parameters from request
    brand = request.GET.get('brand')
    price_range = request.GET.get('price')

    # Apply brand filter if provided
    if brand:
        brand_list = brand.split(',')
        mancloth = mancloth.filter(brand__in=brand_list)

    # Apply price range filter if provided
    if price_range == 'below':
        mancloth = mancloth.filter(discounted_price__lt=1000)
    elif price_range == 'above':
        mancloth = mancloth.filter(discounted_price__gt=1000)

    totalitems = 0
    if request.user.is_authenticated:
        for item in Cart.objects.filter(user=request.user):
            totalitems += item.quantity

    return render(request, 'app/mancloth.html', {'mancloth': mancloth, 'totalitem': totalitems})


def womancloth(request):
    womancloth = Product.objects.filter(category='W')
    
    # Get filter parameters from request
    brand = request.GET.get('brand')
    price_range = request.GET.get('price')

    # Apply brand filter if provided
    if brand:
        brand_list = brand.split(',')
        womancloth = womancloth.filter(brand__in=brand_list)

    # Apply price range filter if provided
    if price_range == 'below':
        womancloth = womancloth.filter(discounted_price__lt=1000)
    elif price_range == 'above':
        womancloth = womancloth.filter(discounted_price__gt=1000)

    totalitems = 0
    if request.user.is_authenticated:
        for item in Cart.objects.filter(user=request.user):
            totalitems += item.quantity

    return render(request, 'app/womancloth.html', {'womancloth': womancloth, 'totalitem': totalitems})

@login_required
def checkout(request):
 #Decrease quantity from product
 if request.method=='POST':
     orders = OrderPlaced.objects.filter(user=request.user)
     totalitems = 0
     for order in orders:
        qty = order.product.quantity
        totalitems += qty
     p = Product.objects.get(id= order.product.pk)
     if(p.quantity==0):
        return HttpResponse("Product outof stock")
     else:
        p.quantity = qty - order.quantity
    #   print(p.quantity)
        p.save()
        return redirect('orders')
     

 user = request.user 
 add = Customer.objects.filter(user=user)
 cart_items = Cart.objects.filter(user=user)
 amount= 0.0 
 shipping_amount = 70.0
 totalamount=0.0
 cart_product = [p for p in Cart.objects.all() if p.user ==request.user]
 for p in cart_product:
  tempamount = (p.quantity * p.product.discounted_price)
  amount += tempamount
 totalamount+=amount + shipping_amount 
 totalitems=0
 for i in Cart.objects.filter(user=request.user):
  totalitems+=i.quantity
 
 

 return render(request, 'app/checkout.html',{'add':add,'totalamount':totalamount,'cartitems': cart_items,'totalitem':totalitems})



@method_decorator(login_required, name='dispatch')
class ProfileView(View):
    def get(self, request):
        user = request.user
        profile = None
        role = None

        if hasattr(user, 'customer'):
            profile = user.customer
            role = 'customer'
        elif hasattr(user, 'seller'):
            profile = user.seller
            role = 'seller'
        elif hasattr(user, 'adminprofile'):
            profile = user.adminprofile
            role = 'admin'
        else:
            profile = user  # Assuming admin or other roles
            role = 'admin'

        totalitems = sum(item.quantity for item in Cart.objects.filter(user=user))

        context = {
            'profile': profile,
            'totalitems': totalitems,
            'role': role
        }
        return render(request, 'app/profile.html', context)


@login_required
def orders(request):
 orders = OrderPlaced.objects.filter(user=request.user)

#  print("refreshed")
 return render(request, 'app/orders.html',{'orderplaced':orders})




# payment system

@login_required
def payment_done(request):
  user = request.user
  # custid = request.GET.get('custid')
  customer = Customer.objects.get(user=user.pk)
  payment = request.GET.get('payment')
  cart = Cart.objects.filter(user=user)
#   uid = uuid4()
  for c in cart:
    OrderPlaced(user=user,  product=c.product, quantity=c.quantity,total=c.total_cost).save()
    if payment == 'e-sewa':
        # return render(request, "app/esewarequest.html",{'total':c.total_cost,'uid':uid} )  
       return redirect('/esewa-request')
      
    elif payment == 'khalti':
        return redirect('/khalti-request' )
    #    return redirect('/khalti-request')
    c.delete()
  return redirect("orders") 

@method_decorator(login_required,name='dispatch')
class KhaltiRequestView(View):
    def get(self, request, *args, **kwargs):
        o_id = requests.GET.get("o_id")
        order = OrderPlaced.objects.get(id=o_id)
        context = {
            "order": order,
        }
        return render(request, "app/khaltirequest.html", context)

@method_decorator(login_required,name='dispatch')
class KhaltiVerifyView(View):
    def get(self, request, *args, **kwargs):
        token = requests.GET.get("token")
        o_id = requests.GET.get("order_id")
        user = request.user
        total = 0
        shipping_cost=70
        cart_items = Cart.objects.filter(user=user)
        
        for item in cart_items:
            total += item.quantity * item.product.discounted_price
        total+=shipping_cost
 

        url = "https://khalti.com/api/v2/payment/verify/"
        payload = {
            "token": token,
            "total": total
        }
        headers = {
            "Authorization": "Key test_secret_key_f59e8b7d18b4499ca40f68195a846e9b"
        }

        order_obj = OrderPlaced.objects.get(id=o_id)

        response = requests.post(url, payload, headers=headers)
        resp_dict = response.json()
        if resp_dict.get("idx"):
            success = True
            order_obj.payment_completed = True
            order_obj.save()
        else:
            success = False
        data = {
            "success": success
        }
        return JsonResponse(data)

# Set up logging
logger = logging.getLogger(__name__)

@method_decorator(login_required, name='dispatch')
class EsewaRequestView(View):
    def get(self, request, *args, **kwargs):
        user = request.user
        uid = uuid4() # Generate a unique ID
        total = 0
        cart_items = Cart.objects.filter(user=user)
        shipping_cost=70
        
        for item in cart_items:
            total += item.quantity * item.product.discounted_price  # Assuming `discounted_price` is the field name for product price

        total=shipping_cost+total 
        return render(request, 'app/esewarequest.html', {'uid': uid, 'total': total})

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
            'scd': 'epay_payment',
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
        
        try:
            order_id = oid.split("_")[1]
            order_obj = OrderPlaced.objects.get(id=order_id)
        except (IndexError, OrderPlaced.DoesNotExist) as e:
            logger.error(f"Order not found: {e}")
            return HttpResponse("Order not found.", status=404)
        
        if status == "Success":
            order_obj.payment_completed = True
            order_obj.save()
            return redirect("/")
        else:
            return redirect(f"/esewa-request/?o_id={order_id}")


# customer registration
class CustomerRegistrationView(View):
  def get(self, request):
        form = CustomerRegistrationForm()
        return render(request, 'app/customerregistration.html', {'form': form})
  
  def post(self, request):
    form = CustomerRegistrationForm(request.POST, request.FILES)
    if form.is_valid():
        user = form.save(commit=False)
        user.phone = form.cleaned_data.get('phone')  # Ensure custom field is saved
        user.image = form.cleaned_data.get('image')  # Ensure custom field is saved
        user = form.save()
        user.is_active =False
        user.save()
        messages.success(request, "Account created successfully! An OTP was sent to your Email")
        return redirect("verify-email", username=request.POST['username'])
    return render(request, 'app/customerregistration.html', {'form': form})
 

def verify_email(request, username):
    user = User.objects.get(username=username)
    user_otp = OtpToken.objects.filter(user=user).last()
    
    
    if request.method == 'POST':
        # valid token
        if user_otp.otp_code == request.POST['otp_code']:
            
            # checking for expired token
            if user_otp.otp_expires_at > timezone.now():
                user.is_active=True
                user.save()
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
    # Another way of varifying email  hhhhhhhhhhhhhhhh
        # user = form.save(commit=False)
        # user.phone = form.cleaned_data.get('phone')  # Ensure custom field is saved
        # user.image = form.cleaned_data.get('image')  # Ensure custom field is saved

    #     user = form.save()
    #     user.is_active =False
    
    #     user.save()

    #     # 
    #     current_site = get_current_site(request)
    #     subject = 'Account verification email'
    #     message = render_to_string('app/email-varification.html', {
    #        'user':user,
    #        'domain':current_site.domain,
    #        'uid':urlsafe_base64_encode(force_bytes(user.pk)),
    #        'token':user_tokenizer_generate.make_token(user),
    #     })

    #     user.email_user(subject=subject , message=message)
    #     return redirect('emailverificationsent')
    #     # return redirect('/accounts/login/')  # Redirect to a success page or some other view
    # return render(request, 'app/customerregistration.html', {'form': form})
 
# def email_verification(request,uidb64,token):
#    unique_id =force_str(urlsafe_base64_decode(uidb64))
#    user=User.objects.get(pk=unique_id)
#    if user and user_tokenizer_generate.check_token(user,token):
#       user.is_active =True
#       user.save()

#       return redirect('emailverificationsuccess')
#    else:
#       return redirect('emailverificationfailed')

# def email_verification_sent(request):
#    return render(request,'app/email-varification-sent.html')

# def email_verification_success(request):
#     return redirect('login_view')

# def email_verification_failed(request):
#     return render(request,'app/email-varification-failed.html')
# hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh


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
            seller_id = request.session.get('seller_id')
            product = form.save(commit=False)
            product.seller = Seller.objects.get(id=seller_id)  # Assuming seller is logged in user
            product.save()
            messages.success(request, 'Product added successfully!')
            return redirect('seller_dashboard')  # Redirect to a seller dashboard or another page
    else:
        form = ProductForm()
    
    return render(request, 'app/seller/add_product.html', {'form': form})

# def joinnow(request):
#    return render(request,'app/seller/link.html')

def aboutus(request):
   return render(request,'app/about.html')

def contactus(request):
   return render(request,'app/contactus.html')


# admin views
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views.generic import View, TemplateView, DetailView, ListView, CreateView
from django.contrib.auth import authenticate, login
from .forms import LoginForm, ProductForm
from .models import Admin, OrderPlaced, Product, ORDER_STATUS



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