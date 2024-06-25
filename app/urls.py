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


    path('add-to-cart/', views.add_to_cart, name='add-to-cart'),
    path('buy/', views.buy_now, name='buynow'),
    path('search/', views.search_view,name='search'),
    path('cart/',views.show_cart, name='showcart'),
    path('pluscart/',views.plus_cart),
    path('minuscart/',views.minus_cart),
    path('removecart/',views.remove_cart,name='removecart'),
    
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('address/', views.address, name='address'),
    path('orders/', views.orders, name='orders'),
    
    path('shoes/', views.shoes, name='shoes'),
    path('shoes/<slug:data>', views.shoes, name='shoesdata'),
    path('cosmetic/', views.cosmetic, name='cosmetic'),
    path('cosmetic/<slug:data>', views.cosmetic, name='cosmeticdata'),
    path('mancloth/', views.mancloth, name='mancloth'),
    path('mancloth/<slug:data>', views.mancloth, name='manclothdata'),
    path('womancloth/', views.womancloth, name='womancloth'),
    path('womancloth/<slug:data>', views.womancloth, name='womanclothdata'),
   

    path('accounts/login/',auth_views.LoginView.as_view(template_name='app/login.html',authentication_form=LoginForm,next_page='home'),name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('passwordchange/', auth_views.PasswordChangeView.as_view(template_name='app/passwordchange.html',form_class=MyPasswordChangeForm , success_url='/passwordchangedone/'),name='passwordchange'),
    path('passwordchangedone/', auth_views.PasswordChangeView.as_view(template_name = 'app/passwordchangedone.html'),name='passwordchangedone'),
    path('password-reset/', auth_views.PasswordResetView.as_view(template_name='app/password_reset.html' , form_class=MyPasswordResetForm), name ='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='app/password_reset_done.html'), name ='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='app/password_reset_confirm.html',form_class=MySetPasswordForm), name ='password_reset_confirm'),
    path('password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(template_name='app/password_reset_complete.html'), name ='password_reset_complete'),
    
    path('registration/', views.CustomerRegistrationView.as_view(), name='customerregistration'),
    
    path('checkout/', views.checkout, name='checkout'),
    path('paymentdone/', views.payment_done ,name='paymentdone'),

    path('category/', views.category.as_view(), name='category'),
    path('newproductdetail/<int:pk>/', views.newproductdetail, name='newproductdetail'),

    


  
# payment urls
   path('khalti-request/', views.KhaltiRequestView.as_view(), name='khalti_request'),
   path('khalti-verify/', views.KhaltiVerifyView.as_view(), name='khalti_verify'),
 

    path('esewa-request/',views.EsewaRequestView.as_view(), name='esewa_request'),
    path('esewa-verify/',views.EsewaVerifyView.as_view(), name='esewa_verify'),


]+ static(settings.MEDIA_URL , document_root=settings.MEDIA_ROOT)

