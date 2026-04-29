"""
Views for the News Application.
Includes API views and traditional Django views for web interface.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Q

from .models import User, Publisher, Article, Newsletter
from .forms import CustomUserCreationForm


def signup(request):
    """Handles user registration using CustomUserCreationForm."""
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
    """Displays landing page with featured approved articles."""
    featured_articles = Article.objects.filter(
        approved=True
    ).order_by('-created_at')[:3]

    return render(request, "landing.html", {
        "featured_articles": featured_articles
    })

# =============================================================================
# API Views
# =============================================================================


@login_required
def api_docs_view(request):
    """Displays API documentation page."""
    return render(request, "api/docs.html")


@login_required
def article_detail_view(request, pk):
    """Displays a single article based on user role permissions."""
    user = request.user

    if user.role == 'Reader':
        article = get_object_or_404(Article, pk=pk, approved=True)
    elif user.role == 'Journalist':
        article = get_object_or_404(Article, pk=pk, author=user)
    else:
        article = get_object_or_404(Article, pk=pk)

    return render(request, 'articles/article_detail.html', {'article': article})


@login_required
def edit_article_view(request, pk):
    """Allows Journalists or Editors to edit articles depending on permissions."""
    user = request.user
    article = get_object_or_404(Article, pk=pk)

    # Check permissions
    if user.role == 'Reader':
        return redirect('article_list')
    if user.role == 'Journalist' and article.author != user:
        return redirect('journalist_dashboard')
    # Editors can edit any article

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
    """Allows Journalists or Editors to delete articles based on permissions."""
    user = request.user
    article = get_object_or_404(Article, pk=pk)

    # Check permissions
    if user.role == 'Reader':
        return redirect('article_list')
    if user.role == 'Journalist' and article.author != user:
        return redirect('journalist_dashboard')
    # Editors can delete any article

    if request.method == 'POST':
        article.delete()
        if user.role == 'Editor':
            return redirect('editor_dashboard')
        return redirect('journalist_dashboard')

    return render(request, 'articles/delete_article.html', {'article': article})


@login_required
def edit_newsletter_view(request, pk):
    """Allows editing of newsletters for Journalists and Editors."""
    user = request.user
    newsletter = get_object_or_404(Newsletter, pk=pk)

    if user.role not in ['Journalist', 'Editor']:
        return redirect('newsletter_list')

    # journalists can only edit their own
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
# Traditional Django Views (Web UI)
# =============================================================================

@login_required
def article_list_view(request):
    """Displays list of articles filtered by user role and subscriptions."""
    user = request.user

    all_articles = Article.objects.filter(approved=True).select_related('author', 'publisher')

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
    """Dashboard for Editors to manage all articles."""
    if request.user.role != 'Editor':
        return redirect('article_list')

    all_articles = Article.objects.all().select_related('author', 'publisher')
    return render(request, 'articles/editor_dashboard.html', {'articles': all_articles})


@login_required
def approve_article_view(request, pk):
    """Allows Editors to approve articles."""
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
    """Dashboard showing Journalist's own articles and newsletters."""
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
    """Allows Journalists to create new articles."""
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

        article = Article.objects.create(
            title=title,
            content=content,
            author=request.user,
            publisher=publisher
        )

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
    """Shows details of a publisher and its approved articles."""
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
    """Displays list of all publishers."""
    publishers = Publisher.objects.all()
    return render(request, 'articles/publisher_list.html', {
        'publishers': publishers
    })


@login_required
def create_newsletter_view(request):
    """Allows Journalists and Editors to create newsletters."""
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

    # Show only approved articles for selection
    articles = Article.objects.filter(approved=True)
    return render(request, 'articles/create_newsletter.html', {
        'articles': articles
    })


@login_required
def newsletter_list_view(request):
    """Displays all newsletters."""
    newsletters = Newsletter.objects.all().select_related('author').prefetch_related('articles')
    return render(request, 'articles/newsletter_list.html', {'newsletters': newsletters})


@login_required
def newsletter_detail_view(request, pk):
    """Displays a single newsletter with its articles."""
    newsletter = get_object_or_404(
        Newsletter.objects
        .select_related('author')
        .prefetch_related('articles', 'articles__author'),
        pk=pk
    )

    articles = newsletter.articles.all()

    return render(request, 'articles/newsletter_detail.html', {
        'newsletter': newsletter,
        'articles': articles
    })


@login_required
def subscribe_publisher_view(request, pk):
    """Toggles subscription to a publisher for Readers."""
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
    """Toggles subscription to a journalist for Readers."""
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
    """Allows Editors to create new publishers."""
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
    """Allows Editors to edit publisher details."""
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
