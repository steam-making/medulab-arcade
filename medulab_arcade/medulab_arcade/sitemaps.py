from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from courses.models import LearningProgram

class StaticViewSitemap(Sitemap):
    priority = 0.8
    changefreq = 'daily'

    def items(self):
        return ['home', 'typing_home', 'student_course_list']

    def location(self, item):
        return reverse(item)

class LearningProgramSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        return LearningProgram.objects.filter(is_active=True)

    def lastmod(self, obj):
        return obj.created_at

    def location(self, obj):
        return obj.get_url()
