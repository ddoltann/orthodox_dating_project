from django import forms
from django.contrib.auth.models import User
from .models import UserProfile, Message, Photo

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ('username', 'first_name', 'email')
        labels = {'username': 'Логин', 'first_name': 'Ваше имя', 'email': 'Электронная почта'}

    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']:
            raise forms.ValidationError('Пароли не совпадают.')
        return cd['password2']
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Этот email уже используется.")
        return email

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'patronymic', 'date_of_birth', 'gender', 'city', 'photo', 'about_me', 'height', 
            'marital_status', 'children', 'education', 'occupation', 'churching_level', 
            'attitude_to_fasting', 'sacraments', 'favorite_saints', 'spiritual_books',
        ]
        widgets = {'date_of_birth': forms.DateInput(attrs={'type': 'date'})}

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        labels = {'first_name': 'Имя', 'last_name': 'Фамилия', 'email': 'Email'}

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = [
            'patronymic', 'date_of_birth', 'gender', 'city', 'photo', 'about_me', 'height', 
            'marital_status', 'children', 'education', 'occupation', 'churching_level', 
            'attitude_to_fasting', 'sacraments', 'favorite_saints', 'spiritual_books',
        ]
        widgets = {'date_of_birth': forms.DateInput(attrs={'type': 'date'})}

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите ваше сообщение...'})
        }
        labels = {'content': ''}

class ProfileFilterForm(forms.Form):
    GENDER_CHOICES = [('', 'Любой')] + list(UserProfile.GENDER_CHOICES)
    CHURCHING_CHOICES = [('', 'Любая')] + list(UserProfile.CHURCHING_LEVEL_CHOICES)
    gender = forms.ChoiceField(label="Пол", choices=GENDER_CHOICES, required=False)
    min_age = forms.IntegerField(label="Возраст от", min_value=18, required=False)
    max_age = forms.IntegerField(label="Возраст до", min_value=18, required=False)
    city = forms.CharField(label="Город", max_length=100, required=False)
    churching_level = forms.ChoiceField(label="Воцерковленность", choices=CHURCHING_CHOICES, required=False)

class PhotoForm(forms.ModelForm):
    class Meta:
        model = Photo
        fields = ['image']
        labels = {'image': 'Выберите файл'}





