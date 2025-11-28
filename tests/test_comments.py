"""
Test cases for Comments API endpoints
- Create comment
- Delete comment
"""
import pytest
from rest_framework import status
from unittest.mock import patch
from blog.models import Comment


@pytest.mark.django_db
class TestCommentAddition:

    def test_successful_comment_addition(self, authenticated_client, create_post):
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

