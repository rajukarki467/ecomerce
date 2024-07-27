from datetime import timezone
import secrets
from django.db import models
from django.contrib.auth.models import User 
from django.core.validators import MaxValueValidator,MinValueValidator
from django.urls import reverse
from django.utils.translation import gettext as _
from django.utils import timezone
from app.validators import validate_mobile_number
from django.contrib.auth.hashers import make_password, check_password

# Create your models here.
STATE_CHOICE = (
    ('Province 1', 'koshi'),
    ('Province 2', 'madesh pradesh'),
    ('Bagmati', 'bagmati'),
    ('Gandaki', 'gandaki'),
    ('Lumbini', 'lumbini'),
    ('Karnali', 'karnali'),
    ('Sudurpashchim', 'sudur_pashchim'),
)
CITY_CHOICE = (
    ('Achham', 'achham'),
    ('Arghakhanchi', 'arghakhanchi'),
    ('Baglung', 'baglung'),
    ('Baitadi', 'baitadi'),
    ('Bajhang', 'bajhang'),
    ('Bajura', 'bajura'),
    ('Banke', 'banke'),
    ('Bara', 'bara'),
    ('Bardiya', 'bardiya'),
    ('Bhaktapur', 'bhaktapur'),
    ('Bhojpur', 'bhojpur'),
    ('Chitwan', 'chitwan'),
    ('Dadeldhura', 'dadeldhura'),
    ('Dailekh', 'dailekh'),
    ('Dang', 'dang'),
    ('Darchula', 'darchula'),
    ('Dhading', 'dhading'),
    ('Dhankuta', 'dhankuta'),
    ('Dhanusha', 'dhanusha'),
    ('Dolakha', 'dolakha'),
    ('Dolpa', 'dolpa'),
    ('Doti', 'doti'),
    ('Gorkha', 'gorkha'),
    ('Gulmi', 'gulmi'),
    ('Humla', 'humla'),
    ('Ilam', 'ilam'),
    ('Jajarkot', 'jajarkot'),
    ('Jhapa', 'jhapa'),
    ('Jumla', 'jumla'),
    ('Kailali', 'kailali'),
    ('Kalikot', 'kalikot'),
    ('Kanchanpur', 'kanchanpur'),
    ('Kapilvastu', 'kapilvastu'),
    ('Kaski', 'kaski'),
    ('Kathmandu', 'kathmandu'),
    ('Kavrepalanchok', 'kavrepalanchok'),
    ('Khotang', 'khotang'),
    ('Lalitpur', 'lalitpur'),
    ('Lamjung', 'lamjung'),
    ('Mahottari', 'mahottari'),
    ('Makwanpur', 'makwanpur'),
    ('Manang', 'manang'),
    ('Morang', 'morang'),
    ('Mugu', 'mugu'),
    ('Mustang', 'mustang'),
    ('Myagdi', 'myagdi'),
    ('Nawalparasi', 'nawalparasi'),
    ('Nuwakot', 'nuwakot'),
    ('Okhaldhunga', 'okhaldhunga'),
    ('Palpa', 'palpa'),
    ('Panchthar', 'panchthar'),
    ('Parbat', 'parbat'),
    ('Parsa', 'parsa'),
    ('Pyuthan', 'pyuthan'),
    ('Ramechhap', 'ramechhap'),
    ('Rasuwa', 'rasuwa'),
    ('Rautahat', 'rautahat'),
    ('Rolpa', 'rolpa'),
    ('Rukum', 'rukum'),
    ('Rupandehi', 'rupandehi'),
    ('Salyan', 'salyan'),
    ('Sankhuwasabha', 'sankhuwasabha'),
    ('Saptari', 'saptari'),
    ('Sarlahi', 'sarlahi'),
    ('Sindhuli', 'sindhuli'),
    ('Sindhupalchok', 'sindhupalchok'),
    ('Siraha', 'siraha'),
    ('Solukhumbu', 'solukhumbu'),
    ('Sunsari', 'sunsari'),
    ('Surkhet', 'surkhet'),
    ('Syangja', 'syangja'),
    ('Tanahun', 'tanahun'),
    ('Taplejung', 'taplejung'),
    ('Terhathum', 'terhathum'),
    ('Udayapur', 'udayapur')
)


class Customer(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    locality = models.CharField(max_length=100)
    city = models.CharField(choices=CITY_CHOICE ,max_length=50)
    state = models.CharField(choices=STATE_CHOICE ,max_length=50)
    phone = models.CharField(max_length=10,null=True,blank=True,validators=[validate_mobile_number])
    image = models.ImageField(upload_to='customer/', null=True, blank=True)

    def __str__(self):
       return str(self.id) 
    

class Seller(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,null=True, blank=True)
    phone = models.CharField(max_length=10,null=False,blank=False,validators=[validate_mobile_number])
    address = models.CharField(max_length=100,null=False,blank=False)
    image = models.ImageField(upload_to='seller/', null=False, blank=False)

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password)
    def __str__(self):
       return str(self.id) 
    

class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100,null=True, blank=True)
    image = models.ImageField(upload_to="admins/", null=False, blank=False)
    mobile = models.CharField(max_length=20,null=False,blank=False,validators=[validate_mobile_number])

    def __str__(self):
        return self.user.username


CATEGORY_CHOICES =   (
    ('M','mans clothes'),
    ('W','womans clothes'),
    ('S','shoes'),
    ('C','cosmetic product'),
)

CATEGORY_MAP = {
    'mens clothes': 'M',
    'men clothes': 'M',
    'men clothes': 'M',
    'men':'M',
    'womans clothes': 'W',
    'women clothes': 'W',
    'woman clothes': 'W',
    'woman':'W',
    'shoes': 'S',
    'footwear': 'S',
    'sneakers': 'S',
    'cosmetic product': 'C',
    'cosmetic': 'C',
    'makeup': 'C',
    'beauty product': 'C',
    'makeup product': 'C',
    'beauty': 'C',
}


class Product(models.Model):
    seller = models.ForeignKey(User,on_delete=models.CASCADE)
    admin = models.ForeignKey(Admin,on_delete=models.CASCADE,null=True, blank=True)
    title =models.CharField(max_length=100)
    selling_price =models.PositiveIntegerField()
    discounted_price = models.PositiveIntegerField()
    description = models.TextField()
    brand = models.CharField(max_length=50)
    category = models.CharField(choices=CATEGORY_CHOICES,max_length=2)
    product_image = models.ImageField(upload_to='prductimg')
    quantity = models.PositiveIntegerField(verbose_name="Quantity",null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True,null=True, blank=True) 
    average_rating = models.FloatField(default=0)  # New field for average rating
    stock_status = models.CharField(max_length=20, default='In Stock')  # New field for stock status
                             
    def __str__(self):
     return str(self.id)
    

    def __str__(self):
      return self.title
    
    def get_absolute_url(self):
        return reverse('product-detail', kwargs={'pk': self.pk})

class LatestProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)

    def __str__(self):
        return self.product.title

    @staticmethod
    def get_latest_products():
        return Product.objects.filter(quantity__gt=0).order_by('-created_at')


class Cart(models.Model):
   user = models.ForeignKey(User , on_delete=models.CASCADE)
   product =models.ForeignKey(Product ,on_delete=models.CASCADE)
   quantity = models.PositiveIntegerField(default=1)

   def __str__(self):
      return str(self.id)
   
   @property
   def total_cost(self):
      return self.quantity * self.product.discounted_price
   


ORDER_STATUS = (
   ('Pending' ,'Pending'),
   ('Delivered','Delivered'),
   ('Cancel','Cancel'),
)

METHOD = (
    ("Cash On Delivery", "Cash On Delivery"),
    ("esewa", "esewa"),
    ("khalti",'khalti'),

)

class OrderPlaced(models.Model):
    user = models.ForeignKey(User, verbose_name="User", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, verbose_name="Product",null=False, on_delete=models.CASCADE)
    address = models.CharField(max_length=200,null=True,blank=True)
    mobile = models.CharField(max_length=10,validators=[validate_mobile_number],blank=False,null=False)
    email = models.EmailField(null=False, blank=False)
    quantity = models.PositiveIntegerField(verbose_name="Quantity")
    total = models.PositiveIntegerField()
    status = models.CharField(max_length=50,default="Pending", choices=ORDER_STATUS)
    ordered_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(
        max_length=20, choices=METHOD, default="Cash On Delivery")
    payment_completed = models.BooleanField(
        default=False, null=True, blank=True)

    def __str__(self):
        return "Order: " + str(self.id)
    
    @property
    def total_cost(self):
        return self.quantity * self.product.discounted_price
    
    def save(self, *args, **kwargs):
        # Automatically calculate and set the total field based on quantity and product price
        self.total = self.total_cost
        super(OrderPlaced, self).save(*args, **kwargs)

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    rating = models.IntegerField()
    review = models.TextField()  # Add this field for the review
    def __str__(self):
        return str(self.user)
    
    
class OtpToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="otps")
    otp_code = models.CharField(max_length=6, default=secrets.token_hex(3))
    tp_created_at = models.DateTimeField(auto_now_add=True)
    otp_expires_at = models.DateTimeField(blank=True, null=True)
    
    
    def __str__(self):
        return self.user.username


class ProductInteraction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    interaction_type = models.CharField(max_length=50)  # e.g.,  "view", "click"
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user} {self.interaction_type} {self.product}'



class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    query = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} - {self.query} - {self.timestamp}'
