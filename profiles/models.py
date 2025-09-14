from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import date
from django.urls import reverse

class UserProfile(models.Model):
    GENDER_CHOICES = (('Мужчина', 'Мужчина'), ('Женщина', 'Женщина'))
    MARITAL_STATUS_CHOICES = (('Не женат/Не замужем', 'Не женат/Не замужем'), ('Разведен(а)', 'Разведен(а)'), ('Вдовец/Вдова', 'Вдовец/Вдова'))
    CHILDREN_CHOICES = (('Нет', 'Нет'), ('Есть', 'Есть'))
    CHURCHING_LEVEL_CHOICES = (('Новоначальный', 'Новоначальный'), ('Воцерковленный', 'Воцерковленный'))
    ATTITUDE_TO_FASTING_CHOICES = (('Соблюдаю', 'Соблюдаю'), ('Не соблюдаю', 'Не соблюдаю'))
    SACRAMENTS_CHOICES = (('Регулярно', 'Регулярно'), ('Иногда', 'Иногда'), ('Редко', 'Редко'))

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    patronymic = models.CharField(max_length=100, blank=True, verbose_name="Отчество")
    date_of_birth = models.DateField(verbose_name="Дата рождения")
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, verbose_name="Пол")
    city = models.CharField(max_length=100, verbose_name="Город")
    photo = models.ImageField(upload_to='profile_pics/%Y/%m/%d/', default='default.jpg', verbose_name="Фотография профиля")
    about_me = models.TextField(blank=True, verbose_name="О себе")
    height = models.PositiveIntegerField(blank=True, null=True, verbose_name="Рост (см)")
    marital_status = models.CharField(max_length=50, choices=MARITAL_STATUS_CHOICES, verbose_name="Семейное положение")
    children = models.CharField(max_length=50, choices=CHILDREN_CHOICES, verbose_name="Дети")
    education = models.CharField(max_length=200, blank=True, verbose_name="Образование")
    occupation = models.CharField(max_length=200, blank=True, verbose_name="Профессия")
    churching_level = models.CharField(max_length=50, choices=CHURCHING_LEVEL_CHOICES, verbose_name="Степень воцерковленности")
    attitude_to_fasting = models.CharField(max_length=50, choices=ATTITUDE_TO_FASTING_CHOICES, verbose_name="Отношение к постам")
    sacraments = models.CharField(max_length=50, choices=SACRAMENTS_CHOICES, verbose_name="Участие в Таинствах")
    favorite_saints = models.CharField(max_length=255, blank=True, verbose_name="Любимые святые")
    spiritual_books = models.TextField(blank=True, verbose_name="Любимые духовные книги")
    is_verified = models.BooleanField(default=False, verbose_name="Верифицирован")

    def __str__(self): return f'Профиль пользователя {self.user.username}'

    @property
    def age(self):
        if self.date_of_birth:
            today = date.today()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return 0

class Like(models.Model):
    user_from = models.ForeignKey(User, related_name='likes_sent', on_delete=models.CASCADE)
    user_to = models.ForeignKey(User, related_name='likes_received', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: unique_together = ('user_from', 'user_to')

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    receiver = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    class Meta: ordering = ['timestamp']

class Photo(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='photos', verbose_name="Профиль пользователя")
    image = models.ImageField(upload_to='photos/%Y/%m/%d/', verbose_name="Фото")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")
    class Meta: verbose_name = "Фотография"; verbose_name_plural = "Фотографии"; ordering = ['-uploaded_at']

class Notification(models.Model):
    NOTIFICATION_TYPES = (('LIKE', 'Новая симпатия'), ('MESSAGE', 'Новое сообщение'))
    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name="Получатель")
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications', verbose_name="Отправитель", null=True, blank=True)
    message = models.TextField(verbose_name="Сообщение")
    notification_type = models.CharField(max_length=10, choices=NOTIFICATION_TYPES, verbose_name="Тип уведомления")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата создания")
    class Meta: verbose_name = "Уведомление"; verbose_name_plural = "Уведомления"; ordering = ['-created_at']
    @property
    def link(self):
        if self.notification_type == 'LIKE' and self.sender: return reverse('profiles:profile_detail', kwargs={'pk': self.sender.pk})
        elif self.notification_type == 'MESSAGE' and self.sender: return reverse('profiles:conversation_detail', kwargs={'pk': self.sender.pk})
        return '#'







