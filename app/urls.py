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
    path('about/',views.aboutus,name='about'),
    path('contactus/',views.contactus,name='contactus'),
    path('chat/',views.chat,name='chat'),


    path('recommendation/',views.recommendations_view,name='recommendation'),
    path('check_stock/<int:product_id>/', views.check_stock, name='check_stock'),

    # cart urls
    path('cart/',views.show_cart, name='showcart'),
    path('pluscart/',views.plus_cart ,name='plus_cart'),
    path('minuscart/',views.minus_cart, name='minus_cart'),
    path('removecart/',views.remove_cart,name='removecart'),
    path('add-to-cart/', views.add_to_cart, name='add-to-cart'),
    
    
    path('profile/', views.ProfileView.as_view(), name='profile'),
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
    path('category/', views.CategoryView.as_view(), name='category'),

    #   registration,login and authentication url
    path('registration/', views.CustomerRegistrationView.as_view(), name='customerregistration'),
    # email varification
    # path('email-varification/<str:uidb64>/<str:token>',views.email_verification,name='email-verification'),
    # path('email-varification-sent/',views.email_verification_sent,name='emailverificationsent'),
    # path('email-varification-success/',views.email_verification_success,name='emailverificationsuccess'),
    # path('email-varification-failed/',views.email_verification_failed,name='emailverificationfailed'),

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

  path('sellerdashboard/', views.seller_dashboard, name='sellerdashboard'),
  path('add-product/', views.add_product, name='add_product'),
  path('sellerhome/', views.sellerhome, name='sellerhome'),
  path('sellerprofile/', views.sellerprofile, name='sellerprofile'),


  # admin 

    # path('admin-login/',views. AdminLoginView.as_view(), name='adminlogin'),
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-home/', views.AdminHomeView.as_view(), name='adminhome'),
    path('deliveredorder/', views.DeliveredOrderView.as_view(), name='deliveredorder'),
    path('cancelorder/', views.CancelOrderView.as_view(), name='cancelorder'),
    path('admin-order/<int:pk>/',views. AdminOrderDetailView.as_view(), name='adminorderdetail'),
    path('admin-orders/', views.AdminOrderListView.as_view(), name='adminorderlist'),
    path('adminorderstatuschange/<int:pk>/',views. AdminOrderStatusChangeView.as_view(), name='adminorderstatuschange'),
    path('admin-products/', views.AdminProductListView.as_view(), name='adminproductlist'),
    path('admin-customer/', views.AdminCustomerListView.as_view(), name='admincustomerlist'),
    path('admin-seller/', views.AdminSellerListView.as_view(), name='adminsellerlist'),
    path('admin-admin/', views.AdminAdminListView.as_view(), name='adminadminlist'),
    # path('admin-product-create/',views.AdminProductCreateView.as_view(), name='adminproductcreate'),
    path('admin-product-create/', views.admin_product_create, name='adminproductcreate'),
    path('admin/product/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    


    path("verify-email/<slug:username>", views.verify_email, name="verify-email"),
    path("resend-otp/", views.resend_otp, name="resend-otp"),
    

   #recommendations from traim data and model
  #  path('recommend/<int:item_id>/', views.recommendationss_view, name='recommend'),
    path('chatbot/', views.chatbot_response, name='chatbot_response'),
    path('customer-info/', views.customer_info, name='customer_info'),
        

    
]+ static(settings.MEDIA_URL , document_root=settings.MEDIA_ROOT)

