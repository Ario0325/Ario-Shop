from django import forms
from .models import ContactMessage


class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'phone', 'subject', 'message']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'cname',
                'placeholder': 'نام خود را وارد کنید *',
                'required': True
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'id': 'cemail',
                'placeholder': 'ایمیل خود را وارد کنید *',
                'required': True
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'cphone',
                'placeholder': 'شماره موبایل خود را وارد کنید'
            }),
            'subject': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'csubject',
                'placeholder': 'موضوع پیام شما'
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control',
                'id': 'cmessage',
                'cols': 30,
                'rows': 4,
                'placeholder': 'متن پیام شما *',
                'required': True,
                'maxlength': '5000',
            }),
        }