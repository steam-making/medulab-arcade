import datetime

from allauth.account.signals import user_signed_up
from django.dispatch import receiver

from .models import UserProfile


@receiver(user_signed_up)
def handle_social_signup(request, user, **kwargs):
    """구글/카카오 등 소셜 로그인으로 처음 가입한 사용자는 이름/생년월일/회원유형 등을
    아직 입력하지 않았으므로 온보딩(추가정보 입력) 페이지로 보내야 한다.
    카카오는 동의된 항목(이름/생일/출생연도/전화번호)을 넘겨주므로 있으면 미리 채워둔다."""
    profile, _ = UserProfile.objects.get_or_create(user=user)

    sociallogin = kwargs.get('sociallogin')
    if sociallogin is not None:
        extra_data = sociallogin.account.extra_data or {}
        kakao_account = extra_data.get('kakao_account', {}) or {}

        name = (
            extra_data.get('name')
            or kakao_account.get('name')
            or extra_data.get('properties', {}).get('nickname')
            or kakao_account.get('profile', {}).get('nickname')
            or ''
        )
        if name and not profile.real_name:
            profile.real_name = name

        birthday = kakao_account.get('birthday')  # 'MMDD'
        birthyear = kakao_account.get('birthyear')  # 'YYYY'
        if birthday and birthyear and not profile.birth_date:
            try:
                profile.birth_date = datetime.date(int(birthyear), int(birthday[:2]), int(birthday[2:]))
            except (ValueError, TypeError):
                pass

        phone_number = kakao_account.get('phone_number')  # 예: '+82 10-1234-5678'
        if phone_number and not profile.phone_number:
            digits = ''.join(ch for ch in phone_number if ch.isdigit())
            if digits.startswith('82'):
                digits = '0' + digits[2:]
            profile.phone_number = digits

        shipping_addresses = kakao_account.get('shipping_addresses') or []
        if shipping_addresses and not profile.address:
            default_addr = next((a for a in shipping_addresses if a.get('is_default')), shipping_addresses[0])
            base = (default_addr.get('base_address') or '').strip()
            detail = (default_addr.get('detail_address') or '').strip()
            address = ' '.join(p for p in (base, detail) if p)
            if address:
                profile.address = address

    profile.onboarding_complete = False
    profile.save()
