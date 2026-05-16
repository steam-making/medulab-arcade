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
    path('program/<int:program_id>/answer-zip/', views.chapter_manage, name='answer_zip_import'),
    path('program/<int:program_id>/answer-zip/<int:batch_id>/apply/', views.answer_zip_apply, name='answer_zip_apply'),
    path('download-template/', views.download_course_template, name='download_course_template'),
    path('program/<int:program_id>/export/', views.export_program_to_excel, name='export_program_to_excel'),
    path('program/<int:program_id>/chapter/add/', views.chapter_create, name='chapter_create'),
    path('chapter/<int:chapter_id>/edit/', views.chapter_edit, name='chapter_edit'),
    path('chapter/<int:chapter_id>/delete/', views.chapter_delete, name='chapter_delete'),
    path('item/<int:item_id>/move/', views.item_move, name='item_move'),
    
    # 아이템 개별 관리
    path('chapter/<int:chapter_id>/item/add/', views.item_create, name='item_create'),
    path('item/<int:item_id>/edit/', views.item_edit, name='item_edit'),
    path('item/<int:item_id>/delete/', views.item_delete, name='item_delete'),
    
    # 학생용
    path('student/courses/', views.student_course_list, name='student_course_list'),
    path('student/homework/', views.student_homework_list, name='student_homework_list'),
    path('student/homework/<int:assignment_id>/submit/', views.student_homework_submit, name='student_homework_submit'),
    path('student/homework/submission/<int:submission_id>/action/', views.homework_submission_action, name='homework_submission_action'),
    path('student/homework/<int:assignment_id>/student/<int:student_id>/complete/', views.homework_assignment_complete, name='homework_assignment_complete'),
    path('student/courses/apply/<int:program_id>/', views.student_course_apply, name='student_course_apply'),
    
    # 학습 흐름
    path('<int:program_id>/', views.course_home, name='course_home'),
    path('chapter/<int:chapter_id>/', views.chapter_detail, name='chapter_detail'),
    path('item/<int:item_id>/', views.item_page, name='item_page'),
    
    # 숙제 관리 (추가)
    path('homework/manage/', views.homework_admin_list, name='homework_admin_list'),
    path('homework/add/', views.homework_create, name='homework_create'),
    path('homework/<int:homework_id>/edit/', views.homework_edit, name='homework_edit'),
    path('homework/<int:homework_id>/delete/', views.homework_delete, name='homework_delete'),
    path('homework/submission/<int:submission_id>/review/', views.homework_submission_review, name='homework_submission_review'),

    # API
    path('api/grade/', views.grade_code, name='grade_code'),
    path('api/item/<int:item_id>/ppt-exam/start/', views.start_ppt_exam, name='start_ppt_exam'),
    path('api/item/<int:item_id>/ppt-exam/submit/', views.submit_ppt_exam, name='submit_ppt_exam'),
    path('api/program/<int:program_id>/structure/', views.api_program_structure, name='api_program_structure'),
    path('api/users/search/', views.api_search_users, name='api_search_users'),
    path('api/program/<int:program_id>/chapters/reorder/', views.api_chapters_reorder, name='api_chapters_reorder'),
    path('api/items/batch-move/', views.api_items_batch_move, name='api_items_batch_move'),
    path('api/program/<int:program_id>/items/reorder/', views.api_items_reorder, name='api_items_reorder'),
]
