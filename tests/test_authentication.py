"""
Test cases for Authentication API endpoints
- Signup
- Login
"""
import pytest
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.authtoken.models import Token
from unittest.mock import patch


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

