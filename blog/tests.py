import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework import status
from unittest.mock import patch, MagicMock
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

    def test_signup_with_mismatched_passwords(self, api_client):
        url = '/api/auth/signup/'
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'newpass123',
            'password_confirm': 'differentpass',
            'first_name': 'New',
            'last_name': 'User',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_signup_with_duplicate_username(self, api_client, create_user):
        create_user(username='existinguser', email='existing@example.com')
        
        url = '/api/auth/signup/'
        data = {
            'username': 'existinguser',
            'email': 'new@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'username' in response.data

    def test_signup_with_duplicate_email(self, api_client, create_user):
        create_user(username='existinguser', email='existing@example.com')
        
        url = '/api/auth/signup/'
        data = {
            'username': 'newuser',
            'email': 'existing@example.com',
            'password': 'newpass123',
            'password_confirm': 'newpass123',
        }
        
        with patch('blog.serializers.send_mail'):
            response = api_client.post(url, data, format='json')
        assert response.status_code == status.HTTP_201_CREATED

    def test_signup_with_short_password(self, api_client):
        url = '/api/auth/signup/'
        data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password': 'short',
            'password_confirm': 'short',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data

    def test_signup_with_missing_fields(self, api_client):
        url = '/api/auth/signup/'
        data = {
            'username': 'newuser',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in response.data or 'password' in response.data


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

    def test_login_with_invalid_email(self, api_client):
        url = '/api/auth/login/'
        data = {
            'email': 'nonexistent@example.com',
            'password': 'somepassword',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data

    def test_login_with_wrong_password(self, api_client, create_user):
        create_user(
            username='loginuser',
            email='login@example.com',
            password='correctpass123',
            is_active=True
        )
        
        url = '/api/auth/login/'
        data = {
            'email': 'login@example.com',
            'password': 'wrongpassword',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data

    def test_login_with_inactive_user(self, api_client, create_user):
        create_user(
            username='inactiveuser',
            email='inactive@example.com',
            password='testpass123',
            is_active=False
        )
        
        url = '/api/auth/login/'
        data = {
            'email': 'inactive@example.com',
            'password': 'testpass123',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'non_field_errors' in response.data

    def test_login_with_missing_fields(self, api_client):
        url = '/api/auth/login/'
        data = {
            'email': 'test@example.com',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'password' in response.data or 'non_field_errors' in response.data


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

    def test_create_private_post(self, authenticated_client):
        url = '/api/posts/'
        data = {
            'title': 'Private Post',
            'content': 'This is a private post.',
            'is_private': True,
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['is_private'] is True
        
        post = Post.objects.get(id=response.data['id'])
        assert post.is_private is True

    def test_post_creation_without_authentication(self, api_client):
        url = '/api/posts/'
        data = {
            'title': 'Unauthorized Post',
            'content': 'This should fail.',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_post_creation_with_missing_title(self, authenticated_client):
        url = '/api/posts/'
        data = {
            'content': 'Content without title.',
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'title' in response.data

    def test_post_creation_with_missing_content(self, authenticated_client):
        url = '/api/posts/'
        data = {
            'title': 'Title without content',
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'content' in response.data

    def test_post_creation_with_empty_title(self, authenticated_client):
        url = '/api/posts/'
        data = {
            'title': '',
            'content': 'Content with empty title',
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'title' in response.data

    def test_post_creation_default_is_private_value(self, authenticated_client):
        url = '/api/posts/'
        data = {
            'title': 'Default Privacy Post',
            'content': 'Testing default privacy setting.',
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['is_private'] is False


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

    def test_comment_on_another_users_post(self, authenticated_client, create_post, create_user):
        another_user = create_user(username='anotheruser', email='another@example.com')
        post = create_post(author=another_user, is_private=False)
        
        url = '/api/comments/'
        data = {
            'post': post.id,
            'comment_text': 'Comment on someone else\'s post.',
        }
        
        with patch('blog.views.send_comment_notification.delay'):
            response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['commenter']['username'] == authenticated_client.user.username

    def test_comment_on_private_post(self, authenticated_client, create_post, create_user):
        another_user = create_user(username='privateuser', email='private@example.com')
        private_post = create_post(author=another_user, is_private=True)
        
        url = '/api/comments/'
        data = {
            'post': private_post.id,
            'comment_text': 'Trying to comment on private post.',
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert 'error' in response.data

    def test_comment_without_authentication(self, api_client, create_post):
        post = create_post()
        
        url = '/api/comments/'
        data = {
            'post': post.id,
            'comment_text': 'Unauthorized comment.',
        }
        
        response = api_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_comment_with_missing_post_id(self, authenticated_client):
        url = '/api/comments/'
        data = {
            'comment_text': 'Comment without post ID.',
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'post' in response.data

    def test_comment_with_missing_text(self, authenticated_client, create_post):
        post = create_post(author=authenticated_client.user)
        
        url = '/api/comments/'
        data = {
            'post': post.id,
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'comment_text' in response.data

    def test_comment_with_empty_text(self, authenticated_client, create_post):
        post = create_post(author=authenticated_client.user)
        
        url = '/api/comments/'
        data = {
            'post': post.id,
            'comment_text': '',
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert 'comment_text' in response.data

    def test_comment_on_nonexistent_post(self, authenticated_client):
        url = '/api/comments/'
        data = {
            'post': 99999,  
            'comment_text': 'Comment on non-existent post.',
        }
        
        response = authenticated_client.post(url, data, format='json')
        
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_404_NOT_FOUND]

    def test_multiple_comments_on_same_post(self, authenticated_client, create_post):
        post = create_post(author=authenticated_client.user)
        
        url = '/api/comments/'
        
        # First comment
        data1 = {
            'post': post.id,
            'comment_text': 'First comment.',
        }
        with patch('blog.views.send_comment_notification.delay'):
            response1 = authenticated_client.post(url, data1, format='json')
        
        # Second comment
        data2 = {
            'post': post.id,
            'comment_text': 'Second comment.',
        }
        with patch('blog.views.send_comment_notification.delay'):
            response2 = authenticated_client.post(url, data2, format='json')
        
        assert response1.status_code == status.HTTP_201_CREATED
        assert response2.status_code == status.HTTP_201_CREATED
        assert response1.data['comment_text'] == 'First comment.'
        assert response2.data['comment_text'] == 'Second comment.'
        
        comments = Comment.objects.filter(post=post)
        assert comments.count() == 2

