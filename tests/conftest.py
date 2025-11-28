
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from blog.models import Post, Comment


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def create_user(db):
    def make_user(**kwargs):
        defaults = {
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'testpass123',
            'is_active': True,
        }
        defaults.update(kwargs)
        password = defaults.pop('password')
        user = User.objects.create_user(**defaults)
        user.set_password(password)
        user.save()
        return user
    return make_user


@pytest.fixture
def authenticated_client(api_client, create_user):
    user = create_user()
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f'Token {token.key}')
    api_client.user = user
    return api_client


@pytest.fixture
def create_post(db, create_user):
    def make_post(**kwargs):
        if 'author' not in kwargs:
            kwargs['author'] = create_user()
        defaults = {
            'title': 'Test Post',
            'content': 'Test content for the post',
            'is_private': False,
        }
        defaults.update(kwargs)
        return Post.objects.create(**defaults)
    return make_post

