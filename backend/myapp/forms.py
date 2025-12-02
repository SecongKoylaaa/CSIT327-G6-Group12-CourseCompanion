# myapp/forms.py

from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = [
            'title',        # Post title
            'description',  # Post content
            'post_type',    # Type of post (e.g., text, image, link)
            'course'        # Associated course
        ]
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter post title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter post description', 'rows': 4}),
            'post_type': forms.Select(attrs={'class': 'form-control'}),
            'course': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter course name'}),
        }
