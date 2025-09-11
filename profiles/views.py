from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from .models import UserProfile, Like, Message, Notification, Photo
from .forms import (
    UserRegistrationForm, UserProfileForm, UserUpdateForm, ProfileUpdateForm,
    MessageForm, ProfileFilterForm, PhotoForm
)

def home_page(request):
    return render(request, 'profiles/home.html')

def register(request):
    if request.method == 'POST':
        user_form = UserRegistrationForm(request.POST)
        profile_form = UserProfileForm(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            profile = profile_form.save(commit=False)
            profile.user = new_user
            profile.save()
            messages.success(request, 'Регистрация прошла успешно! Теперь вы можете войти.')
            return redirect('login')
    else:
        user_form = UserRegistrationForm()
        profile_form = UserProfileForm()
    return render(request, 'profiles/register.html', {'user_form': user_form, 'profile_form': profile_form})

@login_required
def profile_list(request):
    profiles = UserProfile.objects.all().exclude(user=request.user)
    form = ProfileFilterForm(request.GET)
    if form.is_valid():
        cd = form.cleaned_data
        if cd.get('gender'): profiles = profiles.filter(gender=cd['gender'])
        if cd.get('city'): profiles = profiles.filter(city__icontains=cd['city'])
        if cd.get('churching_level'): profiles = profiles.filter(churching_level=cd['churching_level'])
        if cd.get('min_age'):
            min_birth_year = timezone.now().year - cd['min_age']
            profiles = profiles.filter(date_of_birth__year__lte=min_birth_year)
        if cd.get('max_age'):
            max_birth_year = timezone.now().year - cd['max_age']
            profiles = profiles.filter(date_of_birth__year__gte=max_birth_year)
    return render(request, 'profiles/profile_list.html', {'profiles': profiles, 'form': form})

@login_required
def profile_detail(request, pk):
    profile_user = get_object_or_404(User, pk=pk)
    profile = profile_user.userprofile
    mutual_like = False
    if request.user.is_authenticated:
        you_like = Like.objects.filter(user_from=request.user, user_to=profile_user).exists()
        they_like = Like.objects.filter(user_from=profile_user, user_to=request.user).exists()
        if you_like and they_like:
            mutual_like = True
    context = {'profile': profile, 'mutual_like': mutual_like}
    return render(request, 'profiles/profile_detail.html', context)

@login_required
def edit_profile(request):
    photo_form = PhotoForm()
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.userprofile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save(); profile_form.save()
                messages.success(request, 'Ваш профиль был успешно обновлен!')
                return redirect('profiles:edit_profile')
        elif 'upload_photo' in request.POST:
            photo_form = PhotoForm(request.POST, request.FILES)
            if photo_form.is_valid():
                photo = photo_form.save(commit=False)
                photo.user_profile = request.user.userprofile
                photo.save()
                messages.success(request, 'Фотография успешно добавлена!')
                return redirect('profiles:edit_profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.userprofile)
    user_photos = request.user.userprofile.photos.all()
    context = {
        'user_form': user_form, 'profile_form': profile_form,
        'photo_form': photo_form, 'user_photos': user_photos,
    }
    return render(request, 'profiles/edit_profile.html', context)

@login_required
def delete_photo(request, photo_id):
    photo = get_object_or_404(Photo, id=photo_id, user_profile=request.user.userprofile)
    if request.method == 'POST':
        photo.delete()
        messages.success(request, 'Фотография была удалена.')
    return redirect('profiles:edit_profile')

@login_required
def add_like(request, pk):
    user_to = get_object_or_404(User, pk=pk)
    like, created = Like.objects.get_or_create(user_from=request.user, user_to=user_to)
    if created:
        messages.success(request, f'Вы выразили симпатию пользователю {user_to.first_name}.')
        Notification.objects.create(
            recipient=user_to, sender=request.user,
            message=f"Пользователь {request.user.first_name} выразил(а) вам симпатию.",
            notification_type='LIKE'
        )
    else: messages.info(request, f'Вы уже выражали симпатию этому пользователю.')
    return redirect('profiles:profile_detail', pk=pk)

@login_required
def inbox(request):
    sent_to_ids = Message.objects.filter(sender=request.user).values_list('receiver_id', flat=True)
    received_from_ids = Message.objects.filter(receiver=request.user).values_list('sender_id', flat=True)
    interlocutor_ids = set(list(sent_to_ids) + list(received_from_ids))
    interlocutors = User.objects.filter(id__in=interlocutor_ids)
    return render(request, 'profiles/inbox.html', {'interlocutors': interlocutors})

@login_required
def conversation_detail(request, pk):
    interlocutor = get_object_or_404(User, pk=pk)
    you_like = Like.objects.filter(user_from=request.user, user_to=interlocutor).exists()
    they_like = Like.objects.filter(user_from=interlocutor, user_to=request.user).exists()
    if not (you_like and they_like):
        messages.error(request, 'Вы можете писать сообщения только пользователям с взаимной симпатией.')
        return redirect('profiles:profile_detail', pk=pk)
    messages_list = Message.objects.filter(
        (Q(sender=request.user) & Q(receiver=interlocutor)) |
        (Q(sender=interlocutor) & Q(receiver=request.user))
    ).order_by('timestamp')
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.sender = request.user
            message.receiver = interlocutor
            message.save()
            Notification.objects.create(
                recipient=interlocutor, sender=request.user,
                message=f"У вас новое сообщение от {request.user.first_name}.",
                notification_type='MESSAGE'
            )
            return redirect('profiles:conversation_detail', pk=pk)
    else: form = MessageForm()
    context = {'interlocutor': interlocutor, 'messages_list': messages_list, 'form': form}
    return render(request, 'profiles/conversation_detail.html', context)

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user)
    notifications.update(is_read=True)
    return render(request, 'profiles/notifications.html', {'notifications': notifications})

@login_required
def get_new_messages(request, pk, last_timestamp):
    """
    Возвращает новые сообщения в формате JSON для AJAX-опроса.
    """
    interlocutor = get_object_or_404(User, pk=pk)
    
    # Преобразуем timestamp из строки в объект datetime
    last_timestamp_dt = timezone.datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))

    messages = Message.objects.filter(
        (Q(sender=request.user, receiver=interlocutor) | Q(sender=interlocutor, receiver=request.user)) &
        Q(timestamp__gt=last_timestamp_dt)
    ).order_by('timestamp')

    messages_data = [{
        'sender_id': msg.sender.id,
        'content': msg.content,
        'timestamp': msg.timestamp.strftime('%H:%M')
    } for msg in messages]
    
    # Получаем последний timestamp, если есть новые сообщения
    new_last_timestamp = messages.last().timestamp.isoformat() if messages.exists() else last_timestamp

    return JsonResponse({'messages': messages_data, 'last_timestamp': new_last_timestamp})

@login_required
def likes_received_list(request):
    """
    Отображает страницу со списком пользователей,
    которые выразили симпатию текущему пользователю.
    """
    # 1. Находим все объекты Like, где получателем является текущий пользователь
    likes = Like.objects.filter(user_to=request.user)
    
    # 2. Из этих лайков получаем ID всех отправителей
    liker_ids = likes.values_list('user_from_id', flat=True)
    
    # 3. Находим профили всех пользователей, которые поставили лайк
    liker_profiles = UserProfile.objects.filter(user_id__in=liker_ids)
    
    context = {
        'profiles': liker_profiles,
    }
    return render(request, 'profiles/likes_received_list.html', context)



