from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from .models import SiteProfile


class AdminSessionJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)

        if user and user.is_staff:
            session_token = validated_token.get("session_token", None)
            if session_token is not None:
                profile = SiteProfile.get_solo()
                if profile.session_token and profile.session_token != session_token:
                    raise AuthenticationFailed("账号已在其他设备登录，请重新登录")

        return user
