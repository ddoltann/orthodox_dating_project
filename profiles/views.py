from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.urls import reverse
from .forms import PhotoForm, UserRegistrationForm, UserProfileForm, UserUpdateForm, ProfileUpdateForm, MessageForm, ProfileFilterForm
from .models import Photo, UserProfile, Like, Message, Notification
from django.db.models import Q
from datetime import date, timedelta


def home_page(request):
    # Your view logic goes here
    return render(request, 'profiles/home.html')

def register(request):
    if request.user.is_authenticated: return redirect('profiles:profile_list')
    if request.method == 'POST':
        user_form, profile_form = UserRegistrationForm(request.POST), UserProfileForm(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            new_user = user_form.save(commit=False); new_user.set_password(user_form.cleaned_data['password']); new_user.save()
            new_profile = profile_form.save(commit=False); new_profile.user = new_user; new_profile.save()
            messages.success(request, 'Регистрация прошла успешно! Теперь вы можете войти.'); return redirect('login')
        else: messages.error(request, 'Пожалуйста, исправьте ошибки в форме.')
    else: user_form, profile_form = UserRegistrationForm(), UserProfileForm()
    return render(request, 'profiles/register.html', {'user_form': user_form, 'profile_form': profile_form})

@login_required
def edit_profile(request):
    photo_form = PhotoForm() # Создаем пустую форму для загрузки фото
    
    if request.method == 'POST':
        # Определяем, какая форма была отправлена
        if 'update_profile' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            profile_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.userprofile)
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
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
        user_update_form = UserUpdateForm(instance=request.user)
        profile_update_form = ProfileUpdateForm(instance=request.user.userprofile)
        user_photos = request.user.userprofile.photos.all()
    return render(request, 'profiles/edit_profile.html', {'user_form': user_update_form, 'profile_form': profile_update_form, 'photo_form': photo_form, 'user_photos': user_photos})

@login_required
def delete_photo(request, photo_id):
    """
    Представление для удаления фотографии.
    """
    photo = get_object_or_404(Photo, id=photo_id, user_profile=request.user.userprofile)
    if request.method == 'POST':
        photo.delete()
        messages.success(request, 'Фотография была удалена.')
    return redirect('profiles:edit_profile')

@login_required
def profile_detail(request, pk):
    user = get_object_or_404(User, pk=pk)
    profile = get_object_or_404(UserProfile, user=user)
    already_liked = Like.objects.filter(user_from=request.user, user_to=user).exists()
    return render(request, 'profiles/profile_detail.html', {'profile': profile, 'already_liked': already_liked})

@login_required
def profile_list(request):
    profiles = UserProfile.objects.exclude(user=request.user)
    form = ProfileFilterForm(request.GET)
    if form.is_valid():
        city, min_age, max_age, gender = form.cleaned_data.get('city'), form.cleaned_data.get('min_age'), form.cleaned_data.get('max_age'), form.cleaned_data.get('gender')
        if city: profiles = profiles.filter(city__icontains=city)
        if min_age: profiles = profiles.filter(date_of_birth__lte=date.today() - timedelta(days=min_age*365.25))
        if max_age: profiles = profiles.filter(date_of_birth__gte=date.today() - timedelta(days=(max_age + 1)*365.25))
        if gender: profiles = profiles.filter(gender=gender)
    return render(request, 'profiles/profile_list.html', {'profiles': profiles, 'form': form})

@login_required
def add_like(request, pk):
    if request.method == 'POST':
        user_to = get_object_or_404(User, pk=pk)
        user_from = request.user
        if user_to == user_from: messages.error(request, 'Вы не можете выразить симпатию самому себе.'); return redirect('profiles:profile_detail', pk=pk)
        like, created = Like.objects.get_or_create(user_from=user_from, user_to=user_to)
        if created:
            Notification.objects.create(user=user_to, message=f'{user_from.first_name} выразил(а) вам симпатию.', link=reverse('profiles:profile_detail', kwargs={'pk': user_from.pk}))
            if Like.objects.filter(user_from=user_to, user_to=user_from).exists():
                messages.success(request, f'Взаимная симпатия с {user_to.first_name}! Теперь вы можете начать общение.')
                Notification.objects.create(user=user_to, message=f'У вас взаимная симпатия с {user_from.first_name}!', link=reverse('profiles:conversation_detail', kwargs={'pk': user_from.pk}))
                Notification.objects.create(user=user_from, message=f'У вас взаимная симпатия с {user_to.first_name}!', link=reverse('profiles:conversation_detail', kwargs={'pk': user_to.pk}))
            else: messages.success(request, f'Вы выразили симпатию {user_to.first_name}.')
        else: messages.info(request, f'Вы уже выражали симпатию этому пользователю.')
    return redirect('profiles:profile_detail', pk=pk)

@login_required
def inbox(request):
    user_ids = Message.objects.filter(Q(sender=request.user) | Q(receiver=request.user)).values_list('sender', 'receiver')
    interlocutor_ids = {s_id if s_id != request.user.id else r_id for s_id, r_id in user_ids}
    interlocutors = User.objects.filter(id__in=interlocutor_ids)
    return render(request, 'profiles/inbox.html', {'interlocutors': interlocutors})

@login_required
def conversation_detail(request, pk):
    interlocutor = get_object_or_404(User, pk=pk)
    messages_list = Message.objects.filter((Q(sender=request.user, receiver=interlocutor) | Q(sender=interlocutor, receiver=request.user))).order_by('timestamp')
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False); message.sender = request.user; message.receiver = interlocutor; message.save()
            Notification.objects.create(user=interlocutor, message=f'Новое сообщение от {request.user.first_name}.', link=reverse('profiles:conversation_detail', kwargs={'pk': request.user.pk}))
            return redirect('profiles:conversation_detail', pk=pk)
    else: form = MessageForm()
    return render(request, 'profiles/conversation_detail.html', {'interlocutor': interlocutor, 'messages_list': messages_list, 'form': form})

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(user=request.user)
    notifications.update(is_read=True)
    return render(request, 'profiles/notifications.html', {'notifications': notifications})
