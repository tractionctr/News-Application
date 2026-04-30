"""
Serializers for the News Application API.

Handles conversion between Django models and JSON for:
- Users
- Publishers
- Articles
- Newsletters
"""

from rest_framework import serializers
from .models import User, Publisher, Article, Newsletter


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for the User model.

    Exposes user profile data including:
    - role
    - subscriptions
    - account metadata
    """

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'role',
            'subscriptions_publishers', 'subscriptions_journalists',
            'date_joined', 'last_login'
        ]
        read_only_fields = ['id', 'date_joined', 'last_login']

    def create(self, validated_data):
        """
        Creates a new user with properly hashed password.

        Also handles optional subscription relationships.
        """
        password = validated_data.pop('password', None)
        subscriptions_publishers = validated_data.pop('subscriptions_publishers', [])
        subscriptions_journalists = validated_data.pop('subscriptions_journalists', [])

        user = User(**validated_data)

        if password:
            user.set_password(password)

        user.save()

        if subscriptions_publishers:
            user.subscriptions_publishers.set(subscriptions_publishers)

        if subscriptions_journalists:
            user.subscriptions_journalists.set(subscriptions_journalists)

        return user


class PublisherSerializer(serializers.ModelSerializer):
    """
    Serializer for Publisher model.

    Includes computed field for journalist count.
    """

    journalist_count = serializers.SerializerMethodField()

    class Meta:
        model = Publisher
        fields = ['id', 'name', 'journalists', 'editors', 'created_at', 'journalist_count']
        read_only_fields = ['id', 'created_at']

    def get_journalist_count(self, obj):
        """
        Returns number of journalists linked to this publisher.
        """
        return obj.journalists.count()


class ArticleSerializer(serializers.ModelSerializer):
    """
    Full serializer for Article model.

    Used for create/update operations.
    Includes author and publisher metadata.
    """

    author_name = serializers.CharField(source='author.username', read_only=True)
    publisher_name = serializers.CharField(source='publisher.name', read_only=True, allow_null=True)

    class Meta:
        model = Article
        fields = [
            'id', 'title', 'content', 'author', 'author_name',
            'publisher', 'publisher_name', 'created_at', 'approved'
        ]
        read_only_fields = ['id', 'created_at', 'approved', 'author']

    def create(self, validated_data):
        """
        Creates a new article.

        Articles are always created as unapproved by default.
        """
        validated_data['approved'] = False
        return super().create(validated_data)


class ArticleListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for article listings.

    Used for list views where full content is unnecessary.
    """

    author_name = serializers.CharField(source='author.username', read_only=True)
    publisher_name = serializers.CharField(source='publisher.name', read_only=True, allow_null=True)

    class Meta:
        model = Article
        fields = ['id', 'title', 'author_name', 'publisher_name', 'created_at']


class NewsletterSerializer(serializers.ModelSerializer):
    """
    Serializer for Newsletter model.

    Includes article count summary.
    """

    author_name = serializers.CharField(source='author.username', read_only=True)
    article_count = serializers.SerializerMethodField()

    class Meta:
        model = Newsletter
        fields = [
            'id', 'title', 'description', 'author', 'author_name',
            'articles', 'created_at', 'article_count'
        ]
        read_only_fields = ['id', 'created_at']

    def get_article_count(self, obj):
        """
        Returns number of articles in this newsletter.
        """
        return obj.articles.count()


class NewsletterDetailSerializer(serializers.ModelSerializer):
    """
    Detailed newsletter serializer.

    Includes nested article list for full content view.
    """

    author_name = serializers.CharField(source='author.username', read_only=True)
    articles = ArticleListSerializer(many=True, read_only=True)

    class Meta:
        model = Newsletter
        fields = [
            'id', 'title', 'description', 'author', 'author_name',
            'articles', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
