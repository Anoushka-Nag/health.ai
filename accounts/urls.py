from django.urls import path
from . import views


urlpatterns = [
    path('', views.index, name='accounts_index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('update_bio/', views.update_bio, name='update_bio'),
    path('update_avatar/', views.update_avatar, name='update_avatar'),
    path('physical/', views.physical_activity_view, name='physical'),
    path('physical/update_steps/', views.update_steps, name='update_steps'),
    path('physical/add_activity/', views.add_physical_activity, name='add_physical_activity'),
    path('sleep/', views.sleep_view, name='sleep'),
    path('nutrition/', views.nutrition_view, name='nutrition'),
    path('yoga/', views.yoga_view, name='yoga'),
    path('chatbot/', views.healio_view, name='chatbot'),
]
