from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from .models import Comment


@shared_task
def send_comment_notification(comment_id):
    """
    Send an email notification to the post author when a comment is added.
    """
    try:
        comment = Comment.objects.select_related("post", "post__author", "commenter").get(id=comment_id)
        post = comment.post
        post_author = post.author
        commenter = comment.commenter

        subject = f"New comment on your post: {post.title}"
        message = f"""
Hello {post_author.get_full_name() or post_author.username},

{commenter.get_full_name() or commenter.username} has commented on your post "{post.title}":

"{comment.comment_text}"

You can view the post and all comments at: http://localhost:8000/api/posts/{post.id}/

Best regards,
Blog App Team
        """.strip()

        send_mail(
            subject=subject,
            message=message,
            from_email=settings.EMAIL_HOST_USER,  
            recipient_list=[post_author.email],
            fail_silently=False,
        )
        return f"Email notification sent to {post_author.email}"
    except Comment.DoesNotExist:
        return f"Comment with id {comment_id} does not exist"
    except Exception as e:
        return f"Error sending email: {str(e)}"

