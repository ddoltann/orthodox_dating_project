from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    # Стало: главная страница теперь ведет на home_page
    path('', views.home_page, name='home'), 
    
    # Было: path('', views.profile_list, name='profile_list')
    # Стало: список анкет теперь доступен по адресу /profiles/
    path('profiles/', views.profile_list, name='profile_list'), 
    
    path('register/', views.register, name='register'),
    path('profile/<int:pk>/', views.profile_detail, name='profile_detail'),
    path('edit/', views.edit_profile, name='edit_profile'),
    path('like/<int:pk>/', views.add_like, name='add_like'),
    path('inbox/', views.inbox, name='inbox'),
    path('conversation/<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('notifications/', views.notification_list, name='notification_list'),
    path('photo/delete/<int:photo_id>/', views.delete_photo, name='delete_photo'),
]
