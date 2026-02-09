from rest_framework.serializers import ModelSerializer
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class UserProfileSerializer(ModelSerializer):

    class Meta:
        model = User
        fields = (
            "id", "username", "email",
            "date_joined", "updated_at", "role",
            "OTP", "is_active", "OTP_only",
        )
        read_only_fields = (
            "id", "email", "date_joined", "username", "updated_at", 
            "role", "is_active",
        )


    def __init__(self, *args, **kwargs):
        # Флаг, который мы передадим из представления
        is_owner = kwargs.pop('is_owner', False) 
        
        super().__init__(*args, **kwargs)

        if not is_owner and self.instance:
            
            private_fields = ('OTP', 'OTP_only', 'updated_at')
            for field_name in private_fields:
                self.fields.pop(field_name, None)

    def update(self, instance, validated_data):
        if (
            "username" in validated_data
            and instance.username != validated_data["username"]
        ):
            instance.last_username_change = timezone.now()

        return super().update(instance, validated_data)