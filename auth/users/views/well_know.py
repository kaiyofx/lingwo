from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
import json
import base64


def rsa_to_jwk(public_key: rsa.RSAPublicKey, kid: str | None = None) -> dict:
    numbers = public_key.public_numbers()
    e = numbers.e
    n = numbers.n

    e_bytes = e.to_bytes((e.bit_length() + 7) // 8, byteorder="big")
    n_bytes = n.to_bytes((n.bit_length() + 7) // 8, byteorder="big")

    # base64url-кодирование
    def base64url_encode(data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")

    jwk = {
        "kty": "RSA",
        "use": "sig",
        "alg": "RS256",
        "n": base64url_encode(n_bytes),
        "e": base64url_encode(e_bytes),
    }

    if kid:
        jwk["kid"] = kid

    return jwk


class JwksView(APIView):
    """
    Эндпоинт для предоставления публичных ключей в формате JWKS.
    """

    permission_classes = ()

    def get(self, request):
        try:

            public_key_pem = settings.SIMPLE_JWT["VERIFYING_KEY"]

            public_key = serialization.load_pem_public_key(
                public_key_pem.encode("utf-8")
            )

            jwk = rsa_to_jwk(public_key)

            return Response({"keys": [jwk]})

        except AttributeError:
            return Response({"detail": "Public key not configured."}, status=500)
        except Exception as e:

            return Response({"detail": f"Error generating JWKS: {str(e)}"}, status=500)
