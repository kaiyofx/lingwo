from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAdminUser
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from ..models import AdminEventType

User = get_user_model()

class TokenRevokeAdminView(APIView):
    permission_classes = (IsAdminUser,) 

    def post(self, request, user_id):
        """
        Отзывает все Refresh Tokens для указанного user_id.
        """
        
        # 1. Получаем пользователя по user_id
        # Если пользователь не найден, Django автоматически вернет 404
        user = get_object_or_404(User, pk=user_id) 
        
        # 2. Находим все активные токены обновления (Outstanding Tokens)
        # OutstandingToken — это таблица со всеми выданными Refresh Tokens
        outstanding_tokens = OutstandingToken.objects.filter(user=user)
        
        if not outstanding_tokens.exists():
            return Response(
                {"detail": f"No outstanding tokens found for user ID {user_id}."},
                status=status.HTTP_200_OK
            )
            
        blacklisted_count = 0
        
        # 3. Заносим каждый токен в черный список
        for token in outstanding_tokens:
            # Проверяем, не находится ли токен уже в черном списке, 
            # чтобы избежать создания дубликатов
            if not BlacklistedToken.objects.filter(token=token).exists():
                BlacklistedToken.objects.create(token=token)
                blacklisted_count += 1
                
        # 4. Формируем ответ
        response_data = {
            "detail": f"Successfully revoked {blacklisted_count} refresh tokens for user ID {user_id}.",
            "revoked_user_id": user_id,
            "total_outstanding": outstanding_tokens.count(),
        }

        # ❗️ Для целей логирования: добавьте ID отозванного пользователя в ответ
        # Это нужно, чтобы ваш декоратор audit_log_action мог его найти (Шаг 3)
        response_data["user_id"] = user_id 
        
        return Response(response_data, status=status.HTTP_200_OK)