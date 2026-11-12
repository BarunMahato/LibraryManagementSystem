from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    total_credits_earned = serializers.IntegerField(read_only=True)
    available_credits = serializers.IntegerField(read_only=True)
    next_credit_unlock_info = serializers.DictField(read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'password',
            'name',
            'email',
            'role',
            'created_at',
            'total_credits_earned',
            'total_credits_spent',
            'available_credits',
            'next_credit_unlock_info',
        ]
        read_only_fields = ['id', 'created_at', 'total_credits_spent']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def validate_role(self, role):
        if role == User.Role.LIBRARIAN and User.objects.filter(role=User.Role.LIBRARIAN).exists():
            raise serializers.ValidationError('A librarian account already exists.')
        return role
