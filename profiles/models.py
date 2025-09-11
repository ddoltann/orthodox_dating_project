from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.utils import timezone
from cloudinary.models import CloudinaryField  # <-- Импортируем CloudinaryField

class UserProfile(models.Model):
    GENDER_CHOICES = (('М', 'Мужской'), ('Ж', 'Женский'))
    MARITAL_STATUS_CHOICES = (('Не женат/Не замужем', 'Не женат/Не замужем'), ('Разведен(а)', 'Разведен(а)'), ('Вдовец/Вдова', 'Вдовец/Вдова'))
    CHILDREN_CHOICES = (('Нет', 'Нет'), ('Есть, живут со мной', 'Есть, живут со мной'), ('Есть, живут отдельно', 'Есть, живут отдельно'))
    CHURCHING_LEVEL_CHOICES = (('Новоначальный', 'Новоначальный'), ('Воцерковленный', 'Воцерковленный'), ('Глубоко верующий', 'Глубоко верующий'))
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    patronymic = models.CharField(max_length=100, blank=True, verbose_name="Отчество")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name="Пол")
    date_of_birth = models.DateField(verbose_name="Дата рождения")
    
    # Заменяем ImageField на CloudinaryField
    photo = CloudinaryField(verbose_name="Фотография") 
    
    city = models.CharField(max_length=100, verbose_name="Город")
    about_me = models.TextField(blank=True, verbose_name="О себе")
    height = models.PositiveIntegerField(blank=True, null=True, verbose_name="Рост (см)")
    marital_status = models.CharField(max_length=50, choices=MARITAL_STATUS_CHOICES, verbose_name="Семейное положение")
    children = models.CharField(max_length=50, choices=CHILDREN_CHOICES, verbose_name="Дети")
    education = models.CharField(max_length=200, blank=True, verbose_name="Образование")
    occupation = models.CharField(max_length=200, blank=True, verbose_name="Профессия/Род деятельности")
    parish = models.CharField(max_length=255, blank=True, verbose_name="Приход, который посещает")
    churching_level = models.CharField(max_length=50, choices=CHURCHING_LEVEL_CHOICES, verbose_name="Степень воцерковленности")
    attitude_to_fasting = models.TextField(blank=True, verbose_name="Отношение к постам")
    sacraments = models.CharField(max_length=50, choices=[('Регулярно', 'Регулярно'), ('Иногда', 'Иногда'), ('Редко', 'Редко')], verbose_name="Участие в Таинствах")
    favorite_saints = models.CharField(max_length=255, blank=True, verbose_name="Любимые святые")
    spiritual_books = models.TextField(blank=True, verbose_name="Любимые духовные книги")
    is_verified = models.BooleanField(default=False, verbose_name="Верифицирован")

    def __str__(self): 
        return f'Профиль пользователя {self.user.username}'
    
    class Meta:
        verbose_name = "Профиль пользователя"
        verbose_name_plural = "Профили пользователей"
    
    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return 0

# Другие модели не изменяются, так как они не связаны напрямую с хранением изображений в вашей текущей реализации.
# Однако, модель Photo тоже нужно будет обновить, заменив image = models.ImageField(...) на image = CloudinaryField(...).

class Like(models.Model):
    user_from = models.ForeignKey(User, related_name='likes_sent', on_delete=models.CASCADE, verbose_name="От кого")
    user_to = models.ForeignKey(User, related_name='likes_received', on_delete=models.CASCADE, verbose_name="Кому")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")

    def __str__(self): 
        return f'{self.user_from.username} -> {self.user_to.username}'
    
    class Meta:
        verbose_name = "Лайк"
        verbose_name_plural = "Лайки" 
        unique_together = ('user_from', 'user_to')

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE, verbose_name="Отправитель")
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE, verbose_name="Получатель")
    content = models.TextField(verbose_name="Текст сообщения")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Время отправки")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")

    def __str__(self): 
        return f'Сообщение от {self.sender.username} к {self.receiver.username}'
    
    class Meta: 
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"
        ordering = ['timestamp']

class Notification(models.Model):
    """
    Модель для хранения уведомлений для пользователей.
    """
    NOTIFICATION_TYPES = (
        ('LIKE', 'Новая симпатия'),
        ('MESSAGE', 'Новое сообщение'),
    )

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name="Получатель")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', verbose_name="Отправитель", null=True, blank=True)
    message = models.TextField(verbose_name="Сообщение")
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, verbose_name="Тип уведомления")
    
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")

    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомления"
        ordering = ['-created_at']

    def __str__(self):
        sender_name = self.sender.username if self.sender else 'Система'
        return f"Уведомление для {self.recipient.username} от {sender_name}"

    @property
    def link(self):
        if self.notification_type == 'LIKE' and self.sender:
            return reverse('profiles:profile_detail', kwargs={'pk': self.sender.pk})
        elif self.notification_type == 'MESSAGE' and self.sender:
            return reverse('profiles:conversation_detail', kwargs={'pk': self.sender.pk})
        return '#'

class Photo(models.Model):
    """
    Модель для хранения фотографий пользователей.
    """
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='photos', verbose_name="Профиль пользователя")
    
    # Заменяем ImageField на CloudinaryField
    image = CloudinaryField('image', verbose_name="Фото")
    
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    class Meta:
        verbose_name = "Фотография"
        verbose_name_plural = "Фотографии"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Фото для {self.user_profile.user.username} от {self.uploaded_at.strftime('%Y-%m-%d')}"


