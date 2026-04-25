"""
Django signals for the News Application.
Handles article approval notifications.
"""
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from .models import Article
import requests


# PRE SAVE -> store old value
@receiver(pre_save, sender=Article)
def store_old_approved(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            instance._old_approved = old.approved
        except sender.DoesNotExist:
            instance._old_approved = False


# POST SAVE -> react to change
@receiver(post_save, sender=Article)
def article_approved_signal(sender, instance, created, **kwargs):
    if created:
        return

    if hasattr(instance, '_old_approved') and not instance._old_approved and instance.approved:
        print("SIGNAL FIRED")

        send_approval_notifications(instance)
        notify_internal_api(instance)


def send_approval_notifications(article):
    """
    Send email notifications to subscribers when article is approved.
    Subscribers include:
    - Readers subscribed to the author (journalist)
    - Readers subscribed to the publisher (if article has publisher)
    """
    from .models import User

    subscriber_emails = set()

    # Get readers subscribed to the journalist (author)
    readers_subscribed_to_journalist = User.objects.filter(
        subscriptions_journalists=article.author,
        role='Reader'
    )
    for reader in readers_subscribed_to_journalist:
        if reader.email:
            subscriber_emails.add(reader.email)

    # Get readers subscribed to the publisher (if article has publisher)
    if article.publisher:
        readers_subscribed_to_publisher = User.objects.filter(
            subscriptions_publishers=article.publisher,
            role='Reader'
        )
        for reader in readers_subscribed_to_publisher:
            if reader.email:
                subscriber_emails.add(reader.email)

    # Send email to all subscribers
    if subscriber_emails:
        subject = f"New Article Approved: {article.title}"
        message = (
            f"A new article has been approved!\n\n"
            f"Title: {article.title}\n"
            f"Author: {article.author.username}\n"
            f"Publisher: {article.publisher.name if article.publisher else 'Independent'}\n\n"
            f"Thank you for subscribing!"
        )
        from_email = getattr(settings, 'EMAIL_HOST_USER', 'noreply@newsapp.com')
        recipient_list = list(subscriber_emails)

        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=recipient_list,
            fail_silently=True,
        )


def notify_internal_api(article):
    """
    Send POST request to internal API endpoint when article is approved.
    Endpoint: /api/approved/
    """
    endpoint = getattr(settings, 'INTERNAL_API_ENDPOINT', 'http://localhost:8000/api/approved/')

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
        # Log error but don't fail the signal
        pass
