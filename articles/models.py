"""
Models for the News Application.
Defines User, Publisher, Article, and Newsletter models with role-based relationships.
"""
from django.db import models
from django.contrib.auth.models import AbstractUser, Group


class User(AbstractUser):
    """
    Custom user model supporting role-based access control.
    Roles: Reader, Journalist, Editor.
    """
    ROLE_CHOICES = (
        ('Reader', 'Reader'),
        ('Journalist', 'Journalist'),
        ('Editor', 'Editor'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Reader')

    # Reader-specific fields (only used when role = 'Reader')
    subscriptions_publishers = models.ManyToManyField(
        'Publisher',
        blank=True,
        related_name='subscribers'
    )
    subscriptions_journalists = models.ManyToManyField(
        'self',
        blank=True,
        symmetrical=False,
        related_name='subscribed_readers'
    )

    def __str__(self):
        return f"{self.username} ({self.role})"

    def save(self, *args, **kwargs):
        """
        Automatically assign user to Django Group based on role.
        Ensures user belongs to exactly one role group.
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            # Remove any existing group memberships
            self.groups.clear()

            # Add to the group matching the role
            group, created = Group.objects.get_or_create(name=self.role)
            self.groups.add(group)


class Publisher(models.Model):
    """
    Represents a news publisher organization.
    Can have journalists and editors assigned.
    """
    name = models.CharField(max_length=200, unique=True)
    journalists = models.ManyToManyField(
        User,
        blank=True,
        related_name='publisher_affiliations'
    )
    editors = models.ManyToManyField(
        User,
        blank=True,
        related_name='editorial_affiliations'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']


class Article(models.Model):
    """
    Represents a news article written by journalists.
    Can optionally belong to a publisher and be approved by editors.
    """
    title = models.CharField(max_length=300)
    content = models.TextField()
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='articles',
        limit_choices_to={'role': 'Journalist'}
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='articles'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def clean(self):
        """
        Validate that article belongs to either journalist OR publisher.
        Author must be a Journalist.
        """
        from django.core.exceptions import ValidationError

        if self.author.role != 'Journalist':
            raise ValidationError('Article author must be a Journalist.')

        # Article must have either author (journalist) or publisher, but logic ensures
        # author is always set - the distinction is whether publisher is also set
        # For independent articles: author set, publisher null
        # For publisher articles: author set (journalist), publisher set

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Articles'


class Newsletter(models.Model):
    """
    Collection of articles curated by journalists or editors.
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='newsletters',
        limit_choices_to={'role__in': ['Journalist', 'Editor']}
    )
    articles = models.ManyToManyField(
        Article,
        blank=True,
        related_name='newsletters'
    )

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Newsletters'
