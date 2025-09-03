from django import forms
from django.contrib.auth.models import User
from .models import Photo, UserProfile, Message

class UserRegistrationForm(forms.ModelForm):
    email = forms.EmailField(max_length=254, required=True, help_text='Обязательное поле.')
    password = forms.CharField(label='Пароль', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Повторите пароль', widget=forms.PasswordInput)
    class Meta: model = User; fields = ('username', 'first_name', 'email')
    def clean_password2(self):
        cd = self.cleaned_data
        if cd['password'] != cd['password2']: raise forms.ValidationError('Пароли не совпадают.')
        return cd['password2']
    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists(): raise forms.ValidationError('Пользователь с таким email уже существует.')
        return email

class UserProfileForm(forms.ModelForm):
    date_of_birth = forms.DateField(label='Дата рождения', widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}), input_formats=['%Y-%m-%d'])
    class Meta: model = UserProfile; exclude = ('user',)

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()
    class Meta: model = User; fields = ['username', 'first_name', 'email']

class ProfileUpdateForm(forms.ModelForm):
    date_of_birth = forms.DateField(label='Дата рождения', widget=forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}), input_formats=['%Y-%m-%d'])
    class Meta: model = UserProfile; exclude = ('user',)

class MessageForm(forms.ModelForm):
    class Meta:
        model = Message; fields = ('content',)
        labels = {'content': ''}
        widgets = {'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Напишите ваше сообщение...'})}

class ProfileFilterForm(forms.Form):
    city = forms.CharField(label='Город', required=False, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Например, Харьков'}))
    min_age = forms.IntegerField(label='Возраст от', required=False, min_value=18, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '18'}))
    max_age = forms.IntegerField(label='Возраст до', required=False, min_value=18, widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '99'}))
    gender = forms.ChoiceField(label='Пол', required=False, choices=(('', 'Любой'),) + UserProfile.GENDER_CHOICES, widget=forms.Select(attrs={'class': 'form-select'}))


class PhotoForm(forms.ModelForm):
    """
    Форма для загрузки фотографий.
    """
    class Meta:
        model = Photo
        fields = ['image']
        labels = {
            'image': 'Выберите файл'
        }