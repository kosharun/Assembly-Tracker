from django import forms
from .models import Meeting, Member
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Organization

class OrganizationRegistrationForm(UserCreationForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)

class MemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['name']


class MeetingForm(forms.ModelForm):
    present_members = forms.ModelMultipleChoiceField(queryset=Member.objects.all(), widget=forms.CheckboxSelectMultiple)
    class Meta:
        model = Meeting
        fields = ['title', 'date', 'present_members']



