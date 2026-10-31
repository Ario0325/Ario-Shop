"""
فرم‌های ماژول محصولات
"""
from django import forms
from .models import ProductReview


class ProductReviewForm(forms.ModelForm):
    """فرم ثبت نظر برای محصول"""

    class Meta:
        model = ProductReview
        fields = ('name', 'email', 'rating', 'title', 'comment')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'نام شما',
                'maxlength': '200',
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'ایمیل شما',
            }),
            'rating': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'عنوان نظر',
                'maxlength': '200',
            }),
            'comment': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'متن نظر خود را بنویسید...',
                'rows': 5,
                'maxlength': '2000',
            }),
        }
        labels = {
            'name': 'نام',
            'email': 'ایمیل',
            'rating': 'امتیاز',
            'title': 'عنوان نظر',
            'comment': 'متن نظر',
        }
