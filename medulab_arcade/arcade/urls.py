from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    re_path(r'^play/(?P<slug>[-\w]+)/$', views.play, name='play'),
    path('upload/', views.upload, name='upload'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('board/notice/', views.board_notice, name='board_notice'),
    path('board/notice/create/', views.board_notice_create, name='board_notice_create'),
    path('board/notice/<int:pk>/', views.board_notice_detail, name='board_notice_detail'),
    path('board/notice/<int:pk>/update/', views.board_notice_update, name='board_notice_update'),
    path('board/notice/<int:pk>/delete/', views.board_notice_delete, name='board_notice_delete'),
    path('board/awards/', views.board_awards, name='board_awards'),
    path('board/awards/create/', views.board_awards_create, name='board_awards_create'),
    path('board/awards/<int:pk>/', views.board_awards_detail, name='board_awards_detail'),
    path('board/awards/<int:pk>/update/', views.board_awards_update, name='board_awards_update'),
    path('board/awards/<int:pk>/delete/', views.board_awards_delete, name='board_awards_delete'),
    path('board/cert/', views.board_cert, name='board_cert'),
    path('board/cert/create/', views.board_cert_create, name='board_cert_create'),
    path('board/cert/<int:pk>/', views.board_cert_detail, name='board_cert_detail'),
    path('board/cert/<int:pk>/update/', views.board_cert_update, name='board_cert_update'),
    path('board/cert/<int:pk>/delete/', views.board_cert_delete, name='board_cert_delete'),
    path('board/certinfo/', views.board_certinfo, name='board_certinfo'),
    path('board/certinfo/create/', views.board_certinfo_create, name='board_certinfo_create'),
    path('board/certinfo/<int:pk>/', views.board_certinfo_detail, name='board_certinfo_detail'),
    path('board/certinfo/<int:pk>/update/', views.board_certinfo_update, name='board_certinfo_update'),
    path('board/certinfo/<int:pk>/delete/', views.board_certinfo_delete, name='board_certinfo_delete'),
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
    path('api/search-users/', views.search_users, name='search_users'),
    path('api/search-certinfos/', views.search_certinfos, name='search_certinfos'),

    # 회원 관리 (관리자 전용)
    path('admin-services/members/', views.member_list, name='member_list'),
    path('admin-services/members/add/', views.member_create, name='member_create'),
    path('admin-services/members/<int:user_id>/approve/', views.member_approve, name='member_approve'),
    path('admin-services/members/<int:user_id>/edit/', views.member_edit, name='member_edit'),
    path('admin-services/members/<int:user_id>/delete/', views.member_delete, name='member_delete'),

    # 일정 관리 (관리자 전용)
    path('admin-services/schedules/', views.schedule_admin_list, name='schedule_admin_list'),
    path('admin-services/schedules/add/', views.schedule_admin_create, name='schedule_admin_create'),
    path('admin-services/schedules/<int:event_id>/edit/', views.schedule_admin_edit, name='schedule_admin_edit'),
    path('admin-services/schedules/<int:event_id>/delete/', views.schedule_admin_delete, name='schedule_admin_delete'),

    # 배지 관리 (관리자 전용)
    path('admin-services/badges/', views.badge_list, name='badge_list'),
    path('admin-services/badges/add/', views.badge_create, name='badge_create'),
    path('admin-services/badges/<int:badge_id>/edit/', views.badge_edit, name='badge_edit'),
    path('admin-services/badges/<int:badge_id>/delete/', views.badge_delete, name='badge_delete'),
]
