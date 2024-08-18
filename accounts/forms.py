from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from accounts import models


class SignUpForm(UserCreationForm):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')


class LoginForm(forms.Form):
    username = forms.CharField(widget=forms.TextInput())
    password = forms.CharField(widget=forms.PasswordInput())


class SleepTrackForm(forms.Form):
    start_time = forms.DateTimeField(widget=forms.DateTimeInput)
    end_time = forms.DateTimeField(widget=forms.DateTimeInput)


class PhysicalActivityForm(forms.ModelForm):
    class Meta:
        model = models.PhysicalActivity
        fields = '__all__'


class NutritionForm(forms.ModelForm):
    class Meta:
        model = models.Nutrition
        fields = ('meal', 'amount', 'time_of_day')
