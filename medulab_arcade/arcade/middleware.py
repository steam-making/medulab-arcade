from django.shortcuts import redirect
from django.urls import reverse


class SocialOnboardingMiddleware:
    """소셜 로그인으로 처음 가입한 사용자가 추가정보(이름/생년월일/회원유형 등)를
    입력하기 전까지는 온보딩 페이지 외 다른 페이지 접근을 막는다."""

    EXEMPT_PATH_PREFIXES = (
        '/onboarding/',
        '/accounts/logout/',
        '/social-auth/',
        '/static/',
        '/media/',
        '/admin/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            profile = getattr(user, 'profile', None)
            if profile and not profile.onboarding_complete:
                if not request.path.startswith(self.EXEMPT_PATH_PREFIXES):
                    return redirect(reverse('social_onboarding'))
        return self.get_response(request)
