from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    re_path(r'^play/(?P<slug>[-\w]+)/$', views.play, name='play'),
    path('upload/', views.upload, name='upload'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('my-projects/', views.my_projects, name='my_projects'),
    path('project/<int:project_id>/preview/', views.project_preview, name='project_preview'),
    path('project/<int:project_id>/delete/', views.delete_project, name='delete_project'),
    path('project/<int:project_id>/edit/', views.edit_project, name='edit_project'),
    path('project/<int:project_id>/approve/', views.approve_project, name='approve_project'),
    path('signup/', views.signup, name='signup'),
    path('signup/confirm/<str:token>/', views.confirm_signup_email, name='confirm_signup_email'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/email-confirm/<str:token>/', views.confirm_email_change, name='confirm_email_change'),

    # AJAX endpoints
    path('api/like/<int:project_id>/', views.toggle_like, name='toggle_like'),
    path('api/bookmark/<int:project_id>/', views.toggle_bookmark, name='toggle_bookmark'),
    path('api/analyze-zip/', views.analyze_zip, name='analyze_zip'),
    path('api/check-username/', views.check_username, name='check_username'),

    # 회원 관리 (관리자 전용)
    path('admin-services/members/', views.member_list, name='member_list'),
    path('admin-services/members/add/', views.member_create, name='member_create'),
    path('admin-services/members/<int:user_id>/approve/', views.member_approve, name='member_approve'),
    path('admin-services/members/<int:user_id>/edit/', views.member_edit, name='member_edit'),
    path('admin-services/members/<int:user_id>/delete/', views.member_delete, name='member_delete'),

    # 배지 관리 (관리자 전용)
    path('admin-services/badges/', views.badge_list, name='badge_list'),
    path('admin-services/badges/add/', views.badge_create, name='badge_create'),
    path('admin-services/badges/<int:badge_id>/edit/', views.badge_edit, name='badge_edit'),
    path('admin-services/badges/<int:badge_id>/delete/', views.badge_delete, name='badge_delete'),
]
