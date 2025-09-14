from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from .models import UserProfile, Like, Message, Notification, Photo
from .forms import (
    UserRegistrationForm, UserProfileForm, UserUpdateForm, ProfileUpdateForm,
    MessageForm, ProfileFilterForm, PhotoForm
)

def home_page(request):
    return render(request, 'profiles/home.html')

def register(request):
    if request.method == 'POST':
        user_form, profile_form = UserRegistrationForm(request.POST), UserProfileForm(request.POST, request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password']); new_user.save()
            profile = profile_form.save(commit=False)
            profile.user = new_user; profile.save()
            messages.success(request, 'Регистрация прошла успешно! Теперь вы можете войти.')
            return redirect('login')
    else: user_form, profile_form = UserRegistrationForm(), UserProfileForm()
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
        if cd.get('min_age'): profiles = profiles.filter(date_of_birth__year__lte=timezone.now().year - cd['min_age'])
        if cd.get('max_age'): profiles = profiles.filter(date_of_birth__year__gte=timezone.now().year - cd['max_age'])
    return render(request, 'profiles/profile_list.html', {'profiles': profiles, 'form': form})

@login_required
def profile_detail(request, pk):
    profile_user = get_object_or_404(User, pk=pk)
    mutual_like = Like.objects.filter(user_from=request.user, user_to=profile_user).exists() and \
                  Like.objects.filter(user_from=profile_user, user_to=request.user).exists()
    return render(request, 'profiles/profile_detail.html', {'profile': profile_user.userprofile, 'mutual_like': mutual_like})

@login_required
def edit_profile(request):
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
                photo = photo_form.save(commit=False); photo.user_profile = request.user.userprofile; photo.save()
                messages.success(request, 'Фотография успешно добавлена!')
                return redirect('profiles:edit_profile')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = ProfileUpdateForm(instance=request.user.userprofile)
    context = {
        'user_form': user_form, 'profile_form': profile_form,
        'photo_form': PhotoForm(), 'user_photos': request.user.userprofile.photos.all(),
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
    _, created = Like.objects.get_or_create(user_from=request.user, user_to=user_to)
    if created:
        messages.success(request, f'Вы выразили симпатию {user_to.first_name}.')
        Notification.objects.create(recipient=user_to, sender=request.user, message=f"{request.user.first_name} выразил(а) вам симпатию.", notification_type='LIKE')
    else: messages.info(request, f'Вы уже выражали симпатию этому пользователю.')
    return redirect('profiles:profile_detail', pk=pk)

@login_required
def inbox(request):
    sent_to = Message.objects.filter(sender=request.user).values_list('receiver', flat=True)
    received_from = Message.objects.filter(receiver=request.user).values_list('sender', flat=True)
    interlocutors = User.objects.filter(id__in=set(list(sent_to) + list(received_from)))
    return render(request, 'profiles/inbox.html', {'interlocutors': interlocutors})

@login_required
def conversation_detail(request, pk):
    interlocutor = get_object_or_404(User, pk=pk)
    if not (Like.objects.filter(user_from=request.user, user_to=interlocutor).exists() and Like.objects.filter(user_from=interlocutor, user_to=request.user).exists()):
        messages.error(request, 'Вы можете писать сообщения только пользователям с взаимной симпатией.')
        return redirect('profiles:profile_detail', pk=pk)
    messages_list = Message.objects.filter( (Q(sender=request.user, receiver=interlocutor) | Q(sender=interlocutor, receiver=request.user)) ).order_by('timestamp')
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False); message.sender = request.user; message.receiver = interlocutor; message.save()
            Notification.objects.create(recipient=interlocutor, sender=request.user, message=f"Новое сообщение от {request.user.first_name}.", notification_type='MESSAGE')
            return redirect('profiles:conversation_detail', pk=pk)
    else: form = MessageForm()
    return render(request, 'profiles/conversation_detail.html', {'interlocutor': interlocutor, 'messages_list': messages_list, 'form': form})

@login_required
def notification_list(request):
    notifications = Notification.objects.filter(recipient=request.user)
    notifications.update(is_read=True)
    return render(request, 'profiles/notifications.html', {'notifications': notifications})

@login_required
def get_new_messages(request, pk, last_timestamp):
    interlocutor = get_object_or_404(User, pk=pk)
    last_ts = timezone.datetime.fromisoformat(last_timestamp.replace('Z', '+00:00'))
    messages_qs = Message.objects.filter( (Q(sender=request.user, receiver=interlocutor) | Q(sender=interlocutor, receiver=request.user)), timestamp__gt=last_ts).order_by('timestamp')
    messages_data = [{'sender_id': m.sender.id, 'content': m.content, 'timestamp': m.timestamp.strftime('%H:%M')} for m in messages_qs]
    new_ts = messages_qs.last().timestamp.isoformat() if messages_qs.exists() else last_timestamp
    return JsonResponse({'messages': messages_data, 'last_timestamp': new_ts})

@login_required
def likes_received_list(request):
    liker_ids = Like.objects.filter(user_to=request.user).values_list('user_from_id', flat=True)
    liker_profiles = UserProfile.objects.filter(user_id__in=liker_ids)
    return render(request, 'profiles/likes_received_list.html', {'profiles': liker_profiles})






