from django.urls import path
from . import views

urlpatterns = [
    path('', views.typing_home, name='typing_home'),
    path('practice/keys/', views.practice_keys, name='practice_keys'),
    path('practice/words/', views.practice_text, {'content_type': 'word'}, name='practice_words'),
    path('practice/short/', views.practice_text, {'content_type': 'short'}, name='practice_short'),
    path('practice/long/<int:pk>/', views.practice_long, name='practice_long'),
    path('api/save-score/', views.save_score, name='save_score'),
    path('ranking/', views.typing_ranking, name='typing_ranking'),
]
