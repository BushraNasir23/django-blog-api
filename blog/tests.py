import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from unittest.mock import patch
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


@pytest.mark.django_db
class TestSignupView:

    def test_successful_signup(self, api_client):
        url = '/api/auth/signup/'
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
            'first_name': 'New',
            'last_name': 'User',
        }
        
        with patch('blog.serializers.send_mail') as mock_send_mail:
            response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert 'message' in response.data
        assert 'user' in response.data
        assert response.data['user']['username'] == 'newuser'
        assert response.data['user']['email'] == 'newuser@example.com'
        
        user = User.objects.get(username='newuser')
        assert user.email == 'newuser@example.com'
        assert user.is_active is False 
        
        mock_send_mail.assert_called_once()


@pytest.mark.django_db
class TestLoginView:

    def test_successful_login(self, api_client, create_user):
        user = create_user(
            username='loginuser',
            email='login@example.com',
            password='loginpass123',
            is_active=True
        )
        
        url = '/api/auth/login/'
        data = {
            'email': 'login@example.com',
            'password': 'loginpass123',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert 'token' in response.data
        assert 'user' in response.data
        assert response.data['user']['username'] == 'loginuser'
        assert response.data['user']['email'] == 'login@example.com'
        token = Token.objects.get(user=user)
        assert response.data['token'] == token.key


@pytest.mark.django_db
class TestPostCreation:

    def test_successful_post_creation(self, authenticated_client):
        url = '/api/posts/'
        data = {
            'title': 'My Test Post',
            'content': 'This is the content of my test post.',
            'is_private': False,
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['title'] == 'My Test Post'
        assert response.data['content'] == 'This is the content of my test post.'
        assert response.data['is_private'] is False
        assert response.data['author']['username'] == authenticated_client.user.username
        
        post = Post.objects.get(id=response.data['id'])
        assert post.title == 'My Test Post'
        assert post.author == authenticated_client.user


@pytest.mark.django_db
class TestCommentAddition:

    def test_successful_comment_addition(self, authenticated_client, create_post):
        """Test successful addition of a comment to a post."""
        post = create_post(author=authenticated_client.user)
        
        url = '/api/comments/'
        data = {
            'post': post.id,
            'comment_text': 'This is a test comment.',
        }
        with patch('blog.views.send_comment_notification.delay') as mock_task:
            response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['comment_text'] == 'This is a test comment.'
        assert response.data['commenter']['username'] == authenticated_client.user.username
        assert response.data['post_title'] == post.title
        
        comment = Comment.objects.get(id=response.data['id'])
        assert comment.comment_text == 'This is a test comment.'
        assert comment.commenter == authenticated_client.user
        assert comment.post == post
        
        mock_task.assert_called_once()
