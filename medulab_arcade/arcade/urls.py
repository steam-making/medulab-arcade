from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    re_path(r'^play/(?P<slug>[-\w]+)/$', views.play, name='play'),
    path('upload/', views.upload, name='upload'),
    path('my-projects/', views.my_projects, name='my_projects'),
    path('project/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('project/<int:project_id>/edit/', views.edit_project, name='edit_project'),
    path('project/<int:project_id>/approve/', views.approve_project, name='approve_project'),
    path('signup/', views.signup, name='signup'),

    # AJAX endpoints
    path('api/like/<int:project_id>/', views.toggle_like, name='toggle_like'),
    path('api/bookmark/<int:project_id>/', views.toggle_bookmark, name='toggle_bookmark'),
    path('api/analyze-zip/', views.analyze_zip, name='analyze_zip'),
]
