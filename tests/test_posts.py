"""
Test cases for Posts API endpoints
- Create post
- List posts
- Retrieve post
"""
import pytest
from rest_framework import status
from blog.models import Post


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

