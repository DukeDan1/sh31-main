"""
URL configuration for conversation_analyzer project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path
from analyzer import views

handler404 = 'analyzer.views.not_found'

urlpatterns = [
    path('', views.login, name='index'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.unspecified_profile, name='unspecified_profile'),
    path('profile/<int:profile_id>/', views.profile, name='profile'),
    path('upload/', views.upload, name='upload'),
    path('settings/', views.settings_view, name='settings'),
    path('messages_view/', views.unspecified_message, name='unspecified_message'),
    path('messages_view/<str:document_id>/', views.messages_view, name='messages_view'),
    path('profile/update_note/<int:profile_id>/',
         views.update_profile_note, name='update_profile_note'),

    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', views.logout, name='logout'),

    path('api/upload-file', views.api_upload_file, name="api_upload_file"),
    path('api/upload-file/accept', views.api_accept_file, name="api_accept_file"),
    path('api/upload-file/reject', views.api_reject_file, name="api_reject_file"),
    path('api/message/<int:message_id>/', views.api_message, name='api_message'),
    path('api/login', views.api_login, name='api_login'),
    path('api/nlp-process', views.api_nlp_process, name='nlp_process'),
    path('api/chatbot', views.api_chatbot, name='api_chatbot'),
    path('api/document-search', views.api_document_search, name='api_document_search'),

    path('admin/', admin.site.urls),

    path('update_query_tracking/', views.update_query_tracking, name='update_query_tracking'),

    path('profile_search/', views.profile_search, name='profile_search'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
