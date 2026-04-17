from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import User
from django.db.models import Q

class EmailOrUsernameModelBackend(ModelBackend):
    """
    아이디(username) 또는 이메일(email)로 로그인을 지원하는 커스텀 인증 백엔드
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        
        try:
            # username 필드가 username이거나 email인 경우 모두 대응
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except User.DoesNotExist:
            # 가입된 유저가 없는 경우 딜레이를 주어 타이밍 공격 방지 (authenticate_user 기본 동작 모방)
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # 이메일 중복이 허용된 구 버전 데이터 대응 (최신 데이터는 유일성 보장 권장)
            user = User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username)).first()

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
