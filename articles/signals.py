"""
Signal handlers for the News Application.

Handles side-effects triggered when an Article is approved:
- Sending email notifications to subscribers
- Notifying internal API endpoint
"""

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Article, Subscription
import requests


@receiver(post_save, sender=Article)
def article_approved_signal(sender, instance, created, **kwargs):
    """
    Triggered after an Article is saved.

    Fires only when an existing article changes state from:
    approved=False → approved=True

    Used to trigger:
    - email notifications
    - internal API update
    """
    if created:
        return

    old = getattr(instance, "_old_approved", None)

    if old is False and instance.approved is True:
        send_approval_notifications(instance)
        notify_internal_api(instance)


@receiver(pre_save, sender=Article)
def store_old_approved(sender, instance, **kwargs):
    """
    Stores previous approval state of an Article before saving.

    This allows detection of state change in post_save signal.
    """
    if instance.pk:
        instance._old_approved = sender.objects.filter(pk=instance.pk)\
            .values_list("approved", flat=True).first()
    else:
        instance._old_approved = False


def send_approval_notifications(article):
    """
    Sends email notifications to all subscribers when an article is approved.

    Subscribers include:
    - Readers subscribed to the article's journalist
    - Readers subscribed to the article's publisher (if applicable)

    Uses Django's send_mail backend.
    """
    emails = set()

    journalist_subs = Subscription.objects.filter(
        journalist=article.author
    ).values_list("subscriber__email", flat=True)

    emails.update(journalist_subs)

    if article.publisher:
        publisher_subs = Subscription.objects.filter(
            publisher=article.publisher
        ).values_list("subscriber__email", flat=True)

        emails.update(publisher_subs)

    emails = [e for e in emails if e]

    if not emails:
        return

    send_mail(
        subject=f"New Article Approved: {article.title}",
        message=f"""
An article has been approved and is now live.

Title: {article.title}
Author: {article.author.username}
Publisher: {article.publisher.name if article.publisher else "Independent"}
""",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=emails,
        fail_silently=False,
    )


def notify_internal_api(article):
    """
    Sends article approval data to an internal API endpoint.

    Used for logging, analytics, or external system sync.
    """
    endpoint = getattr(
        settings,
        'INTERNAL_API_ENDPOINT',
        'http://localhost:8000/api/approved/'
    )

    payload = {
        'article_id': article.id,
        'title': article.title,
        'author': article.author.username,
        'publisher': article.publisher.name if article.publisher else None,
        'approved': True,
    }

    try:
        requests.post(endpoint, json=payload, timeout=5)
    except requests.RequestException:
        # Fail silently so approval process is not blocked
        pass
