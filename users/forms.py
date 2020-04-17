from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from .models import UserInfo


class CustomUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm):
        model = UserInfo
        fields = ('email',)


class CustomUserChangeForm(UserChangeForm):
    class Meta:
        model = UserInfo
        fields = ('email',)
