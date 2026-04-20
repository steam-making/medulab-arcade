from django.urls import path
from . import views

urlpatterns = [
    path('', views.typing_home, name='typing_home'),
    path('practice/keys/', views.practice_keys, name='practice_keys'),
    path('practice/words/', views.practice_text, {'content_type': 'word'}, name='practice_words'),
    path('practice/short/', views.practice_text, {'content_type': 'short'}, name='practice_short'),
    path('practice/long/', views.practice_long, name='practice_long_select'),
    path('practice/long/<int:pk>/', views.practice_long, name='practice_long'),
    path('api/save-score/', views.save_score, name='save_score'),
    path('api/translate/', views.translate_api, name='translate_api'),
    path('ranking/', views.typing_ranking, name='typing_ranking'),
    
    # 관리자 전용
    path('manage/', views.content_manage, name='typing_content_manage'),
    path('manage/add/', views.content_edit, name='typing_content_create'),
    path('manage/edit/<int:pk>/', views.content_edit, name='typing_content_edit'),
    path('manage/delete/<int:pk>/', views.content_delete, name='typing_content_delete'),
]
