from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserProfile(models.Model):
    GENDER_CHOICES = (('М', 'Мужской'), ('Ж', 'Женский'))
    MARITAL_STATUS_CHOICES = (('Не женат/Не замужем', 'Не женат/Не замужем'), ('Разведен(а)', 'Разведен(а)'), ('Вдовец/Вдова', 'Вдовец/Вдова'))
    CHILDREN_CHOICES = (('Нет', 'Нет'), ('Есть, живут со мной', 'Есть, живут со мной'), ('Есть, живут отдельно', 'Есть, живут отдельно'))
    CHURCHING_LEVEL_CHOICES = (('Новоначальный', 'Новоначальный'), ('Воцерковленный', 'Воцерковленный'), ('Глубоко верующий', 'Глубоко верующий'))
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="Пользователь")
    patronymic = models.CharField(max_length=100, blank=True, verbose_name="Отчество")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, verbose_name="Пол")
    date_of_birth = models.DateField(verbose_name="Дата рождения")
    photo = models.ImageField(upload_to='profile_pics/', default='profile_pics/default.jpg', verbose_name="Фотография")
    city = models.CharField(max_length=100, verbose_name="Город")
    about_me = models.TextField(blank=True, verbose_name="О себе")
    marital_status = models.CharField(max_length=50, choices=MARITAL_STATUS_CHOICES, verbose_name="Семейное положение")
    children = models.CharField(max_length=50, choices=CHILDREN_CHOICES, verbose_name="Дети")
    education = models.CharField(max_length=200, blank=True, verbose_name="Образование")
    occupation = models.CharField(max_length=200, blank=True, verbose_name="Профессия/Род деятельности")
    parish = models.CharField(max_length=255, blank=True, verbose_name="Приход, который посещает")
    churching_level = models.CharField(max_length=50, choices=CHURCHING_LEVEL_CHOICES, verbose_name="Степень воцерковленности")
    attitude_to_fasting = models.TextField(blank=True, verbose_name="Отношение к постам")
    sacraments_participation = models.TextField(blank=True, verbose_name="Участие в таинствах (Исповедь, Причастие)")
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
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications', verbose_name="Пользователь")
    message = models.CharField(max_length=255, verbose_name="Сообщение")
    is_read = models.BooleanField(default=False, verbose_name="Прочитано")
    link = models.URLField(blank=True, null=True, verbose_name="Ссылка")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Время создания")

    def __str__(self): 
        return f'Уведомление для {self.user.username}: "{self.message}"'
    
    class Meta:
        verbose_name = "Уведомление"
        verbose_name_plural = "Уведомлениях" 
        ordering = ['-created_at']

class Photo(models.Model):
    """
    Модель для хранения фотографий пользователей.
    """
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='photos', verbose_name="Профиль пользователя")
    image = models.ImageField(upload_to='photos/%Y/%m/%d/', verbose_name="Фото")
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата загрузки")

    class Meta:
        verbose_name = "Фотография"
        verbose_name_plural = "Фотографии"
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"Фото для {self.user_profile.user.username} от {self.uploaded_at.strftime('%Y-%m-%d')}"
