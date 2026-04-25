"""
Views for the News Application.
Includes API views and traditional Django views for web interface.
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError

from .models import User, Publisher, Article, Newsletter
from .forms import CustomUserCreationForm


def signup(request):
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
    return render(request, "api/docs.html")


@login_required
def edit_article_view(request, pk):
    """Edit an article - Journalists can edit own, Editors can edit any."""
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
    """Delete an article - Journalists can delete own, Editors can delete any."""
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
    """Homepage view showing list of approved articles."""
    articles = Article.objects.filter(approved=True).select_related('author', 'publisher')
    return render(request, 'articles/article_list.html', {'articles': articles})


@login_required
def article_detail_view(request, pk):
    """Article detail view."""
    user = request.user

    if user.role == 'Reader':
        article = get_object_or_404(Article, pk=pk, approved=True)
    elif user.role == 'Journalist':
        article = get_object_or_404(Article, pk=pk, author=user)
    else:  # Editor
        article = get_object_or_404(Article, pk=pk)

    return render(request, 'articles/article_detail.html', {'article': article})


@login_required
def editor_dashboard_view(request):
    """Editor dashboard showing all articles for management."""
    if request.user.role != 'Editor':
        return redirect('article_list')

    all_articles = Article.objects.all().select_related('author', 'publisher')
    return render(request, 'articles/editor_dashboard.html', {'articles': all_articles})


@login_required
def approve_article_view(request, pk):
    """Editor view to approve an article."""
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
    """Journalist dashboard showing their articles and newsletters."""
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
    publishers = Publisher.objects.all()
    return render(request, 'articles/publisher_list.html', {
        'publishers': publishers
    })


@login_required
def create_newsletter_view(request):
    """Create a newsletter - Journalists and Editors can create."""
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
    """List all newsletters."""
    newsletters = Newsletter.objects.all().select_related('author').prefetch_related('articles')
    return render(request, 'articles/newsletter_list.html', {'newsletters': newsletters})


@login_required
def newsletter_detail_view(request, pk):
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
