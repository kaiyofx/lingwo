from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Q
from rest_framework.exceptions import NotFound
from ..serializers import OTPTokenObtainSerializer, OTPSendSerializer
from ..models import ABSUser, AuthType
from ..otp_utils import generate_and_send_otp
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken, Token
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.permissions import IsAuthenticated


class OTPTokenObtainPairView(TokenObtainPairView):
    serializer_class = OTPTokenObtainSerializer

    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class SendOTPView(APIView):
    permission_classes = [AllowAny]
    serializer_class = OTPSendSerializer

    @staticmethod
    def generate_and_send_otp(email: str, auth_type: AuthType) -> Response:
        if not isinstance(email, str):
            raise TypeError("Expected email to be a string.")
        return generate_and_send_otp(email, auth_type)

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        validated_data = serializer.validated_data
        if not isinstance(validated_data, dict):
            raise TypeError("Expected serializer.validated_data to be a dictionary.")
        email = validated_data.get("email")
        username = validated_data.get("username")
        auth_type: AuthType = validated_data["auth_type"]
        target_email = email

        if auth_type == AuthType.LOGIN:
            # --- LOGIN ---
            query = Q()
            if email:
                query |= Q(email__iexact=email)
            if username:
                query |= Q(username_iexact=username)

            try:
                user = ABSUser.objects.get(query)
            except ABSUser.DoesNotExist:
                raise NotFound(detail="User with these credentials does not exist.")
            target_email = user.email
        if not target_email:
            raise Exception("Target email is missing after validation.")

        return self.generate_and_send_otp(target_email, auth_type)


class LogoutView(APIView):
    authentication_classes = (JWTAuthentication,)
    permission_classes = (IsAuthenticated) 

    def post(self, request, *args, **kwargs):
        """
        Принимает refresh token в теле запроса и заносит его в черный список.
        """
        try:
            refresh_token = request.data["refresh"] 

            token = RefreshToken(refresh_token)

            token.blacklist()

            return Response({"detail": "Successfully logged out."}, status=status.HTTP_200_OK)

        except KeyError:
            return Response(
                {"detail": "Refresh token must be provided in the request body."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except TokenError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": "An unexpected error occurred during logout."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)