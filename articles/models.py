"""
Models for the News Application.
Defines User, Publisher, Article, Newsletter, and Subscription models
with role-based relationships and content approval workflow.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.core.exceptions import ValidationError


class User(AbstractUser):
    """
    Custom user model with role-based access control.

    Roles:
    - Reader: consumes content
    - Journalist: creates articles
    - Editor: approves and manages content

    Also supports subscriptions to publishers and journalists.
    """

    ROLE_CHOICES = (
        ('Reader', 'Reader'),
        ('Journalist', 'Journalist'),
        ('Editor', 'Editor'),
    )

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='Reader')
    email = models.EmailField(unique=True)

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
        Saves user and assigns them to a Django Group based on role.
        Ensures each user belongs to a single role group.
        """
        is_new = self.pk is None
        super().save(*args, **kwargs)

        if is_new:
            self.groups.clear()
            group, created = Group.objects.get_or_create(name=self.role)
            self.groups.add(group)


class Publisher(models.Model):
    """
    Represents a news publisher/organization.

    Publishers can have multiple journalists and editors assigned.
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
    News article created by a journalist and optionally associated with a publisher.

    Articles must be approved before becoming publicly visible.
    """

    title = models.CharField(max_length=300)
    content = models.TextField()
    author = models.ForeignKey(User, null=True, blank=True, on_delete=models.CASCADE)
    publisher = models.ForeignKey(Publisher, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def __str__(self):
        return self.title

    def clean(self):
        """
        Validates article ownership rules:
        - Must belong to either author OR publisher context correctly
        - Author must always be a Journalist
        """
        if not self.author:
            raise ValidationError("Article must have an author.")

        if self.author.role != "Journalist":
            raise ValidationError("Author must be a Journalist.")

    def save(self, *args, **kwargs):
        """
        Saves article and triggers approval workflow if status changes to approved.
        """
        is_new_approval = False

        if self.pk:
            old = Article.objects.filter(pk=self.pk).first()
            is_new_approval = (not old.approved and self.approved)

        self.clean()
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Articles'


class Newsletter(models.Model):
    """
    Curated collection of articles created by Journalists or Editors.

    Used to group related news content.
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


class Subscription(models.Model):
    """
    Represents a Reader's subscription to either:
    - a Publisher OR
    - a Journalist

    Only one target type is allowed per subscription.
    """

    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name="subscriptions")
    publisher = models.ForeignKey(Publisher, on_delete=models.CASCADE, null=True, blank=True)
    journalist = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="journalist_subscribers")

    def clean(self):
        """
        Ensures subscription targets exactly one entity type.
        """
        if bool(self.publisher) == bool(self.journalist):
            raise ValidationError("Subscription must be either publisher OR journalist, not both or neither.")

    def save(self, *args, **kwargs):
        """
        Validates and saves subscription.
        """
        self.clean()
        super().save(*args, **kwargs)
