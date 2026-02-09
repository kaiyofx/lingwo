from oauth2_provider.views.base import TokenView
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.response import Response
from .otp_utils import verify_otp
from .models import ABSUser, AuthType
from .forms import OTPTokenForm
from .utils import find_user

User = ABSUser()

@method_decorator(csrf_exempt, name='dispatch')
class OTPTokenView(TokenView):

    def post(self, request, *args, **kwargs):
        print(request.POST)
        form = OTPTokenForm(request.POST)
        if not form.is_valid():
            return Response(
                {'error': 'Неверные данные формы.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user_email = form.cleaned_data.get('user_email')
        username = form.cleaned_data.get('username')
        otp_code = form.cleaned_data.get('otp_code')
        
        user = find_user(user_email, username)
        if isinstance(user, Response):
            return user
        
        if not user.otp:
            return super().post(request, *args, **kwargs)

        if not (user_email or username) or not otp_code:
            return Response(
                {'error': 'Отсутствует OTP или имя пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not verify_otp(user.email, otp_code, AuthType.LOGIN):
            return Response(
                {'error': 'Недействительный или просроченный OTP.'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        return super().post(request, *args, **kwargs)