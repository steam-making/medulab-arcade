from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from .sitemaps import StaticViewSitemap, LearningProgramSitemap

sitemaps = {
    'static': StaticViewSitemap,
    'programs': LearningProgramSitemap,
}

from django.contrib.auth import views as auth_views
from arcade.forms import EmailOrUsernameAuthenticationForm

urlpatterns = [
    path('admin/', admin.site.urls),
    # 로그인 폼 커스터마이징을 위해 개별 선언 (ID/이메일 지원)
    path('accounts/login/', auth_views.LoginView.as_view(authentication_form=EmailOrUsernameAuthenticationForm), name='login'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('courses/', include('courses.urls')),
    path('typing/', include('typing_practice.urls')),
    path('', include('arcade.urls')),
    
    # SEO 및 로봇 관련
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', TemplateView.as_view(template_name="robots.txt", content_type="text/plain")),
]

if settings.DEBUG:
    from django.views.static import serve
    from django.urls import re_path
    urlpatterns += [
        re_path(r'^media/(?P<path>.*)$', serve, {
            'document_root': settings.MEDIA_ROOT,
        }),
    ]