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
    path('profile/', views.profile_view, name='profile'),

    # AJAX endpoints
    path('api/like/<int:project_id>/', views.toggle_like, name='toggle_like'),
    path('api/bookmark/<int:project_id>/', views.toggle_bookmark, name='toggle_bookmark'),
    path('api/analyze-zip/', views.analyze_zip, name='analyze_zip'),
    path('api/check-username/', views.check_username, name='check_username'),

    # 회원 관리 (관리자 전용)
    path('admin-services/members/', views.member_list, name='member_list'),
    path('admin-services/members/add/', views.member_create, name='member_create'),
    path('admin-services/members/<int:user_id>/edit/', views.member_edit, name='member_edit'),
    path('admin-services/members/<int:user_id>/delete/', views.member_delete, name='member_delete'),
]
