from django.contrib import admin
from django.contrib.auth.forms import AuthenticationForm
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Post, Comment

class EmailAuthenticationForm(AuthenticationForm):
    """Custom login form that uses email instead of username"""
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'autofocus': True, 'placeholder': 'Enter your email'})
    )

    def clean(self):
        email = self.cleaned_data.get('username')  # 'username' field contains email
        password = self.cleaned_data.get('password')

        if email is not None and password:
            try:
                user = User.objects.get(email=email)
                self.user_cache = authenticate(
                    self.request,
                    username=user.username,
                    password=password
                )
                if self.user_cache is None:
                    raise forms.ValidationError(
                        self.error_messages['invalid_login'],
                        code='invalid_login',
                        params={'username': self.username_field.verbose_name},
                    )
                else:
                    self.confirm_login_allowed(self.user_cache)
            except User.DoesNotExist:
                raise forms.ValidationError(
                    self.error_messages['invalid_login'],
                    code='invalid_login',
                    params={'username': self.username_field.verbose_name},
                )

        return self.cleaned_data

admin.site.login_form = EmailAuthenticationForm


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "is_private", "created_at"]
    list_filter = ["is_private", "created_at"]
    search_fields = ["title", "content", "author__username", "author__email"]


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ["post", "commenter", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["comment_text", "commenter__username", "commenter__email", "post__title"]
