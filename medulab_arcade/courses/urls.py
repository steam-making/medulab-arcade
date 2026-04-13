from django.urls import path
from . import views

urlpatterns = [
    # 관리자용 - 과정 관리
    path('learning/', views.learning_program_list, name='learning_program_list'),
    path('learning/add/', views.learning_program_create, name='learning_program_create'),
    path('learning/<int:program_id>/edit/', views.learning_program_edit, name='learning_program_edit'),
    path('learning/<int:program_id>/delete/', views.learning_program_delete, name='learning_program_delete'),
    
    # 관리자용 - 유형 관리
    path('types/', views.program_type_list, name='program_type_list'),
    path('types/add/', views.program_type_create, name='program_type_create'),
    path('types/<int:type_id>/edit/', views.program_type_edit, name='program_type_edit'),
    path('types/<int:type_id>/delete/', views.program_type_delete, name='program_type_delete'),

    # 관리자용 - 데이터 관리
    path('program/<int:program_id>/manage/', views.chapter_manage, name='chapter_manage'),
    path('download-template/', views.download_course_template, name='download_course_template'),
    
    # 아이템 개별 관리
    path('chapter/<int:chapter_id>/item/add/', views.item_create, name='item_create'),
    path('item/<int:item_id>/edit/', views.item_edit, name='item_edit'),
    path('item/<int:item_id>/delete/', views.item_delete, name='item_delete'),
    
    # 학생용
    path('student/courses/', views.student_course_list, name='student_course_list'),
    path('student/courses/apply/<int:program_id>/', views.student_course_apply, name='student_course_apply'),
    
    # 학습 흐름
    path('<int:program_id>/', views.course_home, name='course_home'),
    path('chapter/<int:chapter_id>/', views.chapter_detail, name='chapter_detail'),
    path('item/<int:item_id>/', views.item_page, name='item_page'),
    
    # API
    path('api/grade/', views.grade_code, name='grade_code'),
]
