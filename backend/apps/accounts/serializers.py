from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

from .models import Profile
from .services import register_user


User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=True)

    # NEW: user selects Student/Teacher (public)
    account_type = serializers.ChoiceField(choices=[User.Role.STUDENT, User.Role.TEACHER], default=User.Role.STUDENT)
    teacher_message = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name", "password", "password2",
                  "account_type", "teacher_message")

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Passwords do not match."})
        # Run Django's configured AUTH_PASSWORD_VALIDATORS (length, common, numeric…).
        try:
            validate_password(attrs["password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})
        email = attrs["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError({"email": "A user with this email already exists."})
        attrs["email"] = email
        return attrs

    def create(self, validated_data):
        return register_user(validated_data=validated_data)





class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("student_class", "college", "avatar", "bio")


class EmailOTPVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)


class EmailOTPResendSerializer(serializers.Serializer):
    email = serializers.EmailField()


class GoogleAuthSerializer(serializers.Serializer):
    id_token = serializers.CharField()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(min_length=6, max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)
    new_password2 = serializers.CharField(write_only=True, min_length=8)

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password2"]:
            raise serializers.ValidationError({"new_password2": "Passwords do not match."})
        try:
            validate_password(attrs["new_password"])
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)})
        return attrs


class TeacherRequestListSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    username = serializers.CharField(source="user.username", read_only=True)
    email = serializers.EmailField(source="user.email", read_only=True)
    role = serializers.CharField(source="user.role", read_only=True)

    class Meta:
        model = Profile
        fields = (
            "id", "user_id", "username", "email", "role",
            "teacher_status", "teacher_message", "teacher_applied_at", "teacher_reviewed_at",
        )


class MeSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(required=False)

    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name", "role", "email_verified", "auth_provider", "profile")
        # email/email_verified/auth_provider must not be self-mutable — changing
        # email here would otherwise carry over a verified flag (verification bypass).
        read_only_fields = ("id", "role", "email", "email_verified", "auth_provider")

    def update(self, instance, validated_data):
        profile_data = validated_data.pop("profile", None)

        # update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # update profile fields
        if profile_data is not None:
            profile = instance.profile
            for attr, value in profile_data.items():
                setattr(profile, attr, value)
            profile.save()

        return instance


class UserAdminListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "role", "is_active", "date_joined")


class UserRoleUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("role",)
