from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Подключаем все URL-адреса из нашего приложения profiles
    path('', include('profiles.urls', namespace='profiles')),
    
    # URL для входа и выхода.
    path('login/', auth_views.LoginView.as_view(template_name='profiles/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(template_name='profiles/logged_out.html'), name='logout'),
]

# Добавляем маршрут для раздачи медиа-файлов в режиме разработки
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



