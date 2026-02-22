from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),# 用户注册接口
    path('login/', views.login_view, name='login'),# 用户登录接口
    path('user/', views.current_user, name='current_user'),# 获取当前用户信息接口
    path('logout/', views.logout_view, name='logout'),# 用户登出接口
]