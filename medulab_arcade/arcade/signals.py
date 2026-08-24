from allauth.account.signals import user_signed_up
from django.dispatch import receiver

from .models import UserProfile


@receiver(user_signed_up)
def handle_social_signup(request, user, **kwargs):
    """구글/카카오 등 소셜 로그인으로 처음 가입한 사용자는 이름/생년월일/회원유형 등을
    아직 입력하지 않았으므로 온보딩(추가정보 입력) 페이지로 보내야 한다."""
    profile, _ = UserProfile.objects.get_or_create(user=user)

    sociallogin = kwargs.get('sociallogin')
    if sociallogin is not None:
        extra_data = sociallogin.account.extra_data or {}
        name = (
            extra_data.get('name')
            or extra_data.get('properties', {}).get('nickname')
            or extra_data.get('kakao_account', {}).get('profile', {}).get('nickname')
            or ''
        )
        if name and not profile.real_name:
            profile.real_name = name

    profile.onboarding_complete = False
    profile.save()
