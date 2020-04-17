from django import forms
from django.contrib.auth.forms import UserCreationForm


class CalUserCreationForm(UserCreationForm):
    user_type = forms.ChoiceField()

    class Meta(UserCreationForm.Meta):
        pass
