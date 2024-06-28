from django.urls import path,include
from django.contrib import admin
from app import views
from django.conf import settings
from django.conf.urls.static import static 
from django.contrib.auth import views as auth_views
from .forms  import LoginForm , MyPasswordChangeForm,MyPasswordResetForm ,MySetPasswordForm

urlpatterns = [
    path('', views.ProductView.as_view(),name="home"),
    path('product-detail/<int:pk>',  views.ProductDetailView.as_view(), name='product-detail'),
    path('buy/', views.buy_now, name='buynow'),
    path('search/', views.search_view,name='search'),
    path('newproductdetail/<int:pk>/', views.newproductdetail, name='newproductdetail'),
    path('about/',views.aboutus,name='about'),
    path('contactus/',views.contactus,name='contactus'),


    # cart urls
    path('cart/',views.show_cart, name='showcart'),
    path('pluscart/',views.plus_cart),
    path('minuscart/',views.minus_cart),
    path('removecart/',views.remove_cart,name='removecart'),
    path('add-to-cart/', views.add_to_cart, name='add-to-cart'),
    
    
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('address/', views.address, name='address'),
    path('orders/', views.orders, name='orders'),
    
    # product category url
    path('shoes/', views.shoes, name='shoes'),
    path('shoes/<slug:data>', views.shoes, name='shoesdata'),
    path('cosmetic/', views.cosmetic, name='cosmetic'),
    path('cosmetic/<slug:data>', views.cosmetic, name='cosmeticdata'),
    path('mancloth/', views.mancloth, name='mancloth'),
    path('mancloth/<slug:data>', views.mancloth, name='manclothdata'),
    path('womancloth/', views.womancloth, name='womancloth'),
    path('womancloth/<slug:data>', views.womancloth, name='womanclothdata'),
    path('category/', views.category.as_view(), name='category'),

    #   registration,login and authentication url
    path('registration/', views.CustomerRegistrationView.as_view(), name='customerregistration'),
    path('login/', views.login_view, name='login_view'),
    path('accounts/login/',auth_views.LoginView.as_view(template_name='app/login.html',authentication_form=LoginForm,next_page='home'),name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('passwordchange/', auth_views.PasswordChangeView.as_view(template_name='app/passwordchange.html',form_class=MyPasswordChangeForm , success_url='/passwordchangedone/'),name='passwordchange'),
    path('passwordchangedone/', auth_views.PasswordChangeView.as_view(template_name = 'app/passwordchangedone.html'),name='passwordchangedone'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='app/password_reset.html' , form_class=MyPasswordResetForm), name ='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='app/password_reset_done.html'), name ='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='app/password_reset_confirm.html',form_class=MySetPasswordForm), name ='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='app/password_reset_complete.html'), name ='password_reset_complete'),
    
    
# payment urls
   path('khalti-request/', views.KhaltiRequestView.as_view(), name='khalti_request'),
   path('khalti-verify/', views.KhaltiVerifyView.as_view(), name='khalti_verify'),
   path('esewa-request/',views.EsewaRequestView.as_view(), name='esewa_request'),
   path('esewa-verify/',views.EsewaVerifyView.as_view(), name='esewa_verify'),
   path('checkout/', views.checkout, name='checkout'),
   path('paymentdone/', views.payment_done ,name='paymentdone'),

 # seller urls
  # path('accounts/seller/login/',views.SellerLoginView.as_view(),name='sellerlogin'),
  path('sellerdashboard/', views.seller_dashboard, name='sellerdashboard'),
  # path('seller/dashboard/', views.sellerdashboard, name='seller_dashboard'),
  # path('seller/registration/', views.SellerRegistrationView.as_view(), name='sellerregistration'),
  path('add-product/', views.add_product, name='add_product'),
  path('sellerhome/', views.sellerhome, name='sellerhome'),
  path('sellerprofile/', views.sellerprofile, name='sellerprofile'),
  path('join_now/',views.joinnow,name='joinnow'),

  # admin 
    # path("admin-login/", views.AdminLoginView.as_view(), name="adminlogin"),
    # path("admin-home/", views.AdminHomeView.as_view(), name="adminhome"),
    # path("admin-order/<int:pk>/", views.AdminOrderDetailView.as_view(),
    #      name="adminorderdetail"),

    # path("admin-all-orders/", views.AdminOrderListView.as_view(), name="adminorderlist"),

    # path("admin-order-<int:pk>-change/",
    #      views.AdminOrderStatuChangeView.as_view(), name="adminorderstatuschange"),

    # path("admin-product/list/", views.AdminProductListView.as_view(),
    #      name="adminproductlist"),
    # path("admin-product/add/", views.AdminProductCreateView.as_view(),
    #      name="adminproductcreate"),


]+ static(settings.MEDIA_URL , document_root=settings.MEDIA_ROOT)

