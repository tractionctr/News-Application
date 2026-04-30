"""
URL configuration for the News Application.

Maps HTTP routes to their corresponding views, including:
- Web pages (articles, publishers, newsletters)
- Authentication routes
- Admin interface
- API endpoints (docs and auth)
"""

from django.urls import path, include
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from . import views


urlpatterns = [
    # =====================
    # CORE WEB PAGES
    # =====================

    path('', views.landing_page, name='landing'),
    path('articles/', views.article_list_view, name='article_list'),
    path('signup/', views.signup, name='signup'),

    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),

    # =====================
    # ARTICLE ROUTES
    # =====================

    path('articles/<int:pk>/', views.article_detail_view, name='article_detail'),
    path('articles/<int:pk>/edit/', views.edit_article_view, name='edit_article'),
    path('articles/<int:pk>/delete/', views.delete_article_view, name='delete_article'),
    path('articles/<int:pk>/approve/', views.approve_article_view, name='approve_article'),
    path('articles/create/', views.create_article_view, name='create_article'),

    # =====================
    # PUBLISHER ROUTES
    # =====================

    path('publishers/<int:pk>/', views.publisher_detail_view, name='publisher_detail'),
    path('publishers/', views.publisher_list_view, name='publisher_list'),
    path('publishers/create/', views.create_publisher_view, name='create_publisher'),
    path('publishers/<int:pk>/edit/', views.edit_publisher_view, name='edit_publisher'),

    path('publishers/<int:pk>/subscribe/', views.subscribe_publisher_view, name='subscribe_publisher'),
    path('journalists/<int:pk>/subscribe/', views.subscribe_journalist_view, name='subscribe_journalist'),

    # =====================
    # DASHBOARDS
    # =====================

    path('editor/dashboard/', views.editor_dashboard_view, name='editor_dashboard'),
    path('journalist/dashboard/', views.journalist_dashboard_view, name='journalist_dashboard'),

    # =====================
    # NEWSLETTERS
    # =====================

    path('newsletters/', views.newsletter_list_view, name='newsletter_list'),
    path('newsletters/create/', views.create_newsletter_view, name='create_newsletter'),
    path('newsletters/<int:pk>/', views.newsletter_detail_view, name='newsletter_detail'),
    path('newsletters/<int:pk>/edit/', views.edit_newsletter_view, name='edit_newsletter'),

    # =====================
    # ADMIN
    # =====================

    path('admin/', admin.site.urls),

    # =====================
    # AUTH
    # =====================

    path('accounts/', include('django.contrib.auth.urls')),

    # =====================
    # API
    # =====================

    path('api/docs/', views.api_docs_view, name='api-docs'),
]