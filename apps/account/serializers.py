from rest_framework import serializers
import random
import datetime
from django.utils.translation import gettext_lazy as _
import pytz
from .utils import Util
from django.contrib.auth import authenticate
from .models import User, UserOtps
from django.utils.encoding import smart_str, force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.password_validation import validate_password
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings
from config import const


class UserRegistrationEmailSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(max_length=255)

    class Meta:
        model = UserOtps
        fields = ["email"]

    def validate(self, attrs):
        email = attrs.get("email")
        user_qs = User.objects.filter(email=email)
        if user_qs.exists():
            raise serializers.ValidationError("User Already Exists!")

        user_otp_qs = UserOtps.objects.filter(email=email)
        if user_otp_qs.exists():
            user_otp = user_otp_qs.last()
            if user_otp.attempts == 0:
                user_otp.delete()
            if pytz.UTC.localize(
                datetime.datetime.now()
            ) - user_otp.created_at > datetime.timedelta(minutes=5):
                user_otp.delete()
            else:
                raise serializers.ValidationError("OTP Already Sent")
        return attrs

    def create(self, validated_data):
        otp = ""
        for _ in range(6):
            otp += str(random.randint(0, 9))
        otp = int(otp)
        subject = "Email OTP"
        to = validated_data.get("email")
        # Use Django template path, not absolute file path
        template_path = "account/emails/email_otp.html"

        # Try to send email, but continue even if it fails
        email_sent = Util.send_html_email(subject, to, template_path, otp)

        # Create the OTP record regardless of email status
        otp_instance = UserOtps.objects.create(
            email=validated_data.get("email"), otp=otp
        )

        # Log if email failed (for debugging)
        if not email_sent:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"OTP created for {to} but email delivery failed. OTP: {otp}"
            )

        return otp_instance


class UserRegistrationSerializer(serializers.ModelSerializer):

    password = serializers.CharField(
        write_only=True, required=False, style={"input_type": "password"}
    )
    password2 = serializers.CharField(
        write_only=True, required=False, style={"input_type": "password"}
    )
    tc = serializers.BooleanField(required=False)
    auth_provider = serializers.CharField(
        write_only=True, required=False, default=const.AUTH_PROVIDERS.get("email")
    )
    otp = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = User
        fields = [
            "email",
            "name",
            "password",
            "password2",
            "tc",
            "auth_provider",
            "otp",
        ]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        password = attrs.get("password")
        password2 = attrs.get("password2")
        otp = int(attrs.get("otp"))

        email = attrs.get("email")
        tc = attrs.get("tc")
        auth_provider = attrs.get("auth_provider", const.AUTH_PROVIDERS.get("email"))

        otp_query = UserOtps.objects.filter(email=email)

        if auth_provider == const.AUTH_PROVIDERS.get("email"):
            # Direct email registration
            if not password or not password2:
                raise serializers.ValidationError(
                    _("Password fields are required for email registration.")
                )
            if password != password2:
                raise serializers.ValidationError(_("Passwords don't match."))
            validate_password(password)
            if tc is not True:
                raise serializers.ValidationError(
                    _("You must accept the terms and conditions.")
                )

            if not otp_query.exists():
                raise serializers.ValidationError("OTP for email doesn't exsist.")
            else:
                otp_obj = otp_query.last()
                if pytz.UTC.localize(
                    datetime.datetime.now()
                ) - otp_obj.created_at > datetime.timedelta(minutes=5):
                    otp_query.delete()
                    raise serializers.ValidationError(
                        "OTP expired!!Please redo the registration process."
                    )

                if otp_obj.otp != otp:
                    if otp_obj.attempts == 1:
                        otp_query.delete()
                        raise serializers.ValidationError(
                            "Too many wrong attemps!!Please redo the registration process."
                        )
                    otp_obj.attempts -= 1
                    otp_obj.save()
                    raise serializers.ValidationError(
                        f"Incorrect OTP,{otp_obj.attempts} Attempts Remaining"
                    )
                else:
                    otp_query.delete()
        else:
            # OAuth registration
            if User.objects.filter(email=email).exists():
                raise serializers.ValidationError(
                    _("User with this email already exists.")
                )
            attrs["tc"] = True  # Assuming terms are accepted via OAuth

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password", None)
        validated_data.pop("password2", None)
        auth_provider = validated_data.pop(
            "auth_provider", const.AUTH_PROVIDERS.get("email")
        )

        user = User(
            email=validated_data["email"],
            name=validated_data["name"],
            tc=validated_data.get("tc", True),
            auth_provider=auth_provider,
            is_email_verify=auth_provider != const.AUTH_PROVIDERS.get("email"),
        )

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        fields = ["email", "password"]

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(username=email, password=password)

        if user:
            if not user.is_active:
                raise serializers.ValidationError(_("User account is disabled."))
            attrs["user"] = user
            return attrs
        else:
            if User.objects.filter(email=email).exists():
                user = User.objects.get(email=email)
                if user.auth_provider != const.AUTH_PROVIDERS.get("email"):
                    raise serializers.ValidationError(
                        _(f"Please continue your login using {user.auth_provider}.")
                    )
            raise serializers.ValidationError(_("Invalid email or password."))


class UserProfileSerializer(serializers.ModelSerializer):
    @staticmethod
    def get_avatar(obj):
        try:
            return obj.avatar.url
        except (AttributeError, ValueError):
            return None

    avatar = serializers.SerializerMethodField("get_avatar")

    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "name",
            "avatar",
            "is_admin",
            "auth_provider",
        ]


class UserChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True, required=False, style={"input_type": "password"}
    )
    new_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    new_password2 = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    class Meta:
        fields = ["old_password", "new_password", "new_password2"]

    def validate(self, attrs):
        user = self.context.get("user")
        old_password = attrs.get("old_password")
        new_password = attrs.get("new_password")
        new_password2 = attrs.get("new_password2")

        if new_password != new_password2:
            raise serializers.ValidationError(_("New passwords don't match."))

        if user.auth_provider == const.AUTH_PROVIDERS.get("email"):
            # For direct login users
            if not user.check_password(old_password):
                raise serializers.ValidationError(_("Old password is incorrect."))
        else:
            # For OAuth users
            if user.has_usable_password():
                if not user.check_password(old_password):
                    raise serializers.ValidationError(_("Old password is incorrect."))
            elif old_password:
                raise serializers.ValidationError(_("No existing password to verify."))

        validate_password(new_password, user=user)
        return attrs

    def save(self, **kwargs):
        user = self.context.get("user")
        new_password = self.validated_data.get("new_password")
        user.set_password(new_password)
        user.save()
        return user


class SendPasswordResetEmailSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=255)

    class Meta:
        fields = ["email"]

    def validate(self, attrs):
        email = attrs.get("email")
        if not User.objects.filter(email=email).exists():
            raise serializers.ValidationError(
                _("There is no user registered with this email address.")
            )

        user = User.objects.get(email=email)
        if user.auth_provider != const.AUTH_PROVIDERS.get("email"):
            raise serializers.ValidationError(
                _(
                    f"Password reset not allowed for {user.auth_provider} sign-in method."
                )
            )

        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = PasswordResetTokenGenerator().make_token(user)
        link = f"{settings.FRONTEND_URL}api/user/reset/" + uid + "/" + token + "/"
        subject = "Reset LINK"
        to = user.email
        # Use Django template path, not absolute file path
        template_path = "account/emails/password_reset.html"

        # Try to send email, but don't fail if it errors
        email_sent = Util.send_html_email(subject, to, template_path, link)

        if not email_sent:
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Password reset token created for {to} but email delivery failed"
            )
            # In production, you might want to raise an error here:
            # raise serializers.ValidationError({"email": "Unable to send reset email. Please try again later."})

        return attrs


class UserPasswordResetSerializer(serializers.Serializer):
    new_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )
    new_password2 = serializers.CharField(
        write_only=True, style={"input_type": "password"}
    )

    class Meta:
        fields = ["new_password", "new_password2"]

    def validate(self, attrs):
        uid = self.context.get("uid")
        token = self.context.get("token")
        new_password = attrs.get("new_password")
        new_password2 = attrs.get("new_password2")

        if new_password != new_password2:
            raise serializers.ValidationError(_("Passwords don't match."))

        try:
            user_id = smart_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            raise serializers.ValidationError(_("Invalid user.")) from e

        if user.auth_provider != const.AUTH_PROVIDERS.get("email"):
            raise serializers.ValidationError(
                _(
                    f"Password reset not allowed for {user.auth_provider} sign-in method."
                )
            )

        if not PasswordResetTokenGenerator().check_token(user, token):
            raise serializers.ValidationError(_("Invalid or expired token."))

        validate_password(new_password, user=user)
        attrs["user"] = user
        return attrs

    def save(self, **kwargs):
        user = self.validated_data["user"]
        new_password = self.validated_data.get("new_password")
        user.set_password(new_password)
        user.save()
        return user
