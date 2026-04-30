"""
Views for the News Application.

Handles all web-facing logic including:
- Authentication (signup/login/logout)
- Article CRUD operations
- Publisher management
- Newsletter management
- Role-based dashboards
- Subscription system
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Q

from .models import User, Publisher, Article, Newsletter
from .forms import CustomUserCreationForm


def signup(request):
    """
    Handles user registration.

    Creates a new user with role selection and redirects to login on success.
    """
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                form.save()
                return redirect("login")
            except IntegrityError:
                form.add_error("username", "Username already exists")
    else:
        form = CustomUserCreationForm()

    return render(request, "registration/signup.html", {"form": form})


def landing_page(request):
    """
    Landing page view.

    Displays featured approved articles.
    """
    featured_articles = Article.objects.filter(
        approved=True
    ).order_by('-created_at')[:3]

    return render(request, "landing.html", {
        "featured_articles": featured_articles
    })


# =============================================================================
# API + CORE ARTICLE VIEWS
# =============================================================================

@login_required
def api_docs_view(request):
    """
    Displays API documentation page.
    """
    return render(request, "api/docs.html")


@login_required
def article_detail_view(request, pk):
    """
    Displays a single article.

    Access rules:
    - Readers: only approved articles
    - Journalists: own articles
    - Admin/Editor: all access
    """
    user = request.user

    if user.role == 'Admin':
        article = get_object_or_404(Article, pk=pk)
    elif user.role == 'Journalist':
        article = get_object_or_404(Article, pk=pk, author=user)
    else:
        article = get_object_or_404(Article, pk=pk, approved=True)

    return render(request, 'articles/article_detail.html', {'article': article})


@login_required
def edit_article_view(request, pk):
    """
    Edit an existing article.

    Permissions:
    - Journalists: only their own articles
    - Editors: any article
    - Readers: no access
    """
    user = request.user
    article = get_object_or_404(Article, pk=pk)

    if user.role == 'Reader':
        return redirect('article_list')
    if user.role == 'Journalist' and article.author != user:
        return redirect('journalist_dashboard')

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        publisher_id = request.POST.get('publisher')

        if not title or not content:
            return render(request, 'articles/edit_article.html', {
                'article': article,
                'error': 'Title and content are required.'
            })

        publisher = None
        if publisher_id:
            publisher = get_object_or_404(Publisher, id=publisher_id)

        article.title = title
        article.content = content
        article.publisher = publisher
        article.save()

        if user.role == 'Editor':
            return redirect('editor_dashboard')
        return redirect('journalist_dashboard')

    publishers = Publisher.objects.all()
    return render(request, 'articles/edit_article.html', {
        'article': article,
        'publishers': publishers
    })


@login_required
def delete_article_view(request, pk):
    """
    Deletes an article.

    Permissions:
    - Journalists: own articles only
    - Editors: any article
    - Readers: no access
    """
    user = request.user
    article = get_object_or_404(Article, pk=pk)

    if user.role == 'Reader':
        return redirect('article_list')
    if user.role == 'Journalist' and article.author != user:
        return redirect('journalist_dashboard')

    if request.method == 'POST':
        article.delete()
        if user.role == 'Editor':
            return redirect('editor_dashboard')
        return redirect('journalist_dashboard')

    return render(request, 'articles/delete_article.html', {'article': article})


@login_required
def edit_newsletter_view(request, pk):
    """
    Edit a newsletter.

    Permissions:
    - Journalists: only their own newsletters
    - Editors: all newsletters
    """
    user = request.user
    newsletter = get_object_or_404(Newsletter, pk=pk)

    if user.role not in ['Journalist', 'Editor']:
        return redirect('newsletter_list')

    if user.role == 'Journalist' and newsletter.author != user:
        return redirect('journalist_dashboard')

    if request.method == 'POST':
        newsletter.title = request.POST.get('title')
        newsletter.description = request.POST.get('description')

        article_ids = request.POST.getlist('articles')
        newsletter.articles.set(article_ids)

        newsletter.save()
        return redirect('newsletter_detail', pk=newsletter.pk)

    articles = Article.objects.filter(approved=True)

    return render(request, 'articles/edit_newsletter.html', {
        'newsletter': newsletter,
        'articles': articles
    })


# =============================================================================
# MAIN CONTENT VIEWS
# =============================================================================

@login_required
def article_list_view(request):
    """
    Displays list of articles.

    Readers see personalized feed based on subscriptions.
    Other roles see all approved articles.
    """
    user = request.user

    all_articles = Article.objects.filter(
        approved=True
    ).select_related('author', 'publisher')

    if user.role == 'Reader':
        subs_pub = user.subscriptions_publishers.all()
        subs_jour = user.subscriptions_journalists.all()

        subscribed = all_articles.filter(
            Q(publisher__in=subs_pub) |
            Q(author__in=subs_jour)
        )

        others = all_articles.exclude(
            id__in=subscribed.values_list('id', flat=True)
        )

        articles = list(subscribed) + list(others)
    else:
        articles = all_articles

    return render(request, 'articles/article_list.html', {
        'articles': articles
    })


@login_required
def editor_dashboard_view(request):
    """
    Editor dashboard.

    Shows all articles for moderation and approval.
    """
    if request.user.role != 'Editor':
        return redirect('article_list')

    all_articles = Article.objects.all().select_related('author', 'publisher')
    return render(request, 'articles/editor_dashboard.html', {'articles': all_articles})


@login_required
def approve_article_view(request, pk):
    """
    Approves an article.

    Triggers notification system via signals.
    """
    if request.user.role != 'Editor':
        return redirect('article_list')

    article = get_object_or_404(Article, pk=pk)

    if request.method == 'POST':
        article.approved = True
        article.save()
        return redirect('editor_dashboard')

    return render(request, 'articles/approve_article.html', {'article': article})


@login_required
def journalist_dashboard_view(request):
    """
    Journalist dashboard.

    Shows:
    - Their articles
    - Their newsletters
    """
    if request.user.role != 'Journalist':
        return redirect('article_list')

    articles = Article.objects.filter(author=request.user)
    newsletters = Newsletter.objects.filter(author=request.user)

    return render(request, 'articles/journalist_dashboard.html', {
        'articles': articles,
        'newsletters': newsletters
    })


@login_required
def create_article_view(request):
    """
    Creates a new article.

    Only journalists can create articles.
    Articles are unapproved by default.
    """
    if request.user.role != 'Journalist':
        return redirect('article_list')

    if request.method == 'POST':
        title = request.POST.get('title')
        content = request.POST.get('content')
        publisher_id = request.POST.get('publisher')
        newsletter_ids = request.POST.getlist('newsletters')

        publisher = None
        if publisher_id:
            publisher = get_object_or_404(Publisher, id=publisher_id)

        article = Article(
            title=title,
            content=content,
            author=request.user,
            publisher=publisher
        )

        article.full_clean()
        article.save()

        if newsletter_ids:
            newsletters = Newsletter.objects.filter(id__in=newsletter_ids)
            for n in newsletters:
                n.articles.add(article)

        return redirect('journalist_dashboard')

    publishers = Publisher.objects.all()
    newsletters = Newsletter.objects.filter(author=request.user)

    return render(request, 'articles/create_article.html', {
        'publishers': publishers,
        'newsletters': newsletters
    })


@login_required
def publisher_detail_view(request, pk):
    """
    Displays a publisher and its approved articles.
    """
    publisher = get_object_or_404(Publisher, pk=pk)

    articles = Article.objects.filter(
        publisher=publisher,
        approved=True
    ).select_related('author')

    return render(request, 'articles/publisher_detail.html', {
        'publisher': publisher,
        'articles': articles
    })


@login_required
def publisher_list_view(request):
    """
    Displays all publishers.
    """
    publishers = Publisher.objects.all()
    return render(request, 'articles/publisher_list.html', {
        'publishers': publishers
    })


@login_required
def create_newsletter_view(request):
    """
    Creates a newsletter.

    Only journalists and editors can create newsletters.
    """
    if request.user.role not in ['Journalist', 'Editor']:
        return redirect('article_list')

    if request.method == 'POST':
        title = request.POST['title']
        description = request.POST['description']
        article_ids = request.POST.getlist('articles')

        newsletter = Newsletter.objects.create(
            title=title,
            description=description,
            author=request.user
        )

        newsletter.articles.set(article_ids)

        return redirect('newsletter_list')

    articles = Article.objects.filter(approved=True)
    return render(request, 'articles/create_newsletter.html', {
        'articles': articles
    })


@login_required
def newsletter_list_view(request):
    """
    Displays all newsletters.
    """
    newsletters = Newsletter.objects.all().select_related('author').prefetch_related('articles')
    return render(request, 'articles/newsletter_list.html', {'newsletters': newsletters})


@login_required
def newsletter_detail_view(request, pk):
    """
    Displays a single newsletter and its approved articles.
    """
    newsletter = get_object_or_404(
        Newsletter.objects
        .select_related('author')
        .prefetch_related('articles', 'articles__author'),
        pk=pk
    )

    articles = newsletter.articles.filter(approved=True)

    return render(request, 'articles/newsletter_detail.html', {
        'newsletter': newsletter,
        'articles': articles
    })


@login_required
def subscribe_publisher_view(request, pk):
    """
    Toggles subscription to a publisher for a reader.
    """
    if request.user.role != 'Reader':
        return redirect('article_list')

    publisher = get_object_or_404(Publisher, pk=pk)

    if publisher in request.user.subscriptions_publishers.all():
        request.user.subscriptions_publishers.remove(publisher)
    else:
        request.user.subscriptions_publishers.add(publisher)

    return redirect('publisher_detail', pk=pk)


@login_required
def subscribe_journalist_view(request, pk):
    """
    Toggles subscription to a journalist for a reader.
    """
    if request.user.role != 'Reader':
        return redirect('article_list')

    journalist = get_object_or_404(User, pk=pk, role='Journalist')

    if journalist in request.user.subscriptions_journalists.all():
        request.user.subscriptions_journalists.remove(journalist)
    else:
        request.user.subscriptions_journalists.add(journalist)

    return redirect('article_list')


@login_required
def create_publisher_view(request):
    """
    Creates a new publisher.

    Only editors can create publishers.
    """
    if request.user.role != 'Editor':
        return redirect('article_list')

    if request.method == 'POST':
        name = request.POST.get('name')

        if name:
            Publisher.objects.create(name=name)
            return redirect('publisher_list')

    return render(request, 'articles/create_publisher.html')


@login_required
def edit_publisher_view(request, pk):
    """
    Edits a publisher.

    Only editors can modify publishers.
    """
    if request.user.role != 'Editor':
        return redirect('publisher_list')

    publisher = get_object_or_404(Publisher, pk=pk)
    articles = Article.objects.filter(publisher=publisher)

    if request.method == 'POST':
        name = request.POST.get('name')

        if name:
            publisher.name = name
            publisher.save()
            return redirect('publisher_detail', pk=pk)

    return render(request, 'articles/edit_publisher.html', {
        'publisher': publisher,
        'articles': articles
    })
