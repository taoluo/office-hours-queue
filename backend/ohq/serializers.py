from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.crypto import get_random_string
from phonenumber_field.serializerfields import PhoneNumberField
from rest_framework import serializers

from ohq.models import Course, Membership, MembershipInvite, Profile, Question, Queue, Semester
from ohq.sms import sendSMSVerification


class CourseRouteMixin(serializers.ModelSerializer):
    """
    Mixin for serializers that overrides the save method to
    properly handle the URL parameter for courses.
    """

    def save(self):
        self.validated_data["course"] = Course.objects.get(
            pk=self.context["view"].kwargs["course_pk"]
        )
        return super().save()


class QueueRouteMixin(serializers.ModelSerializer):
    """
    Mixin for serializers that overrides the save method to
    properly handle the URL parameter for queues.
    """

    def save(self):
        self.validated_data["queue"] = Queue.objects.get(pk=self.context["view"].kwargs["queue_pk"])
        return super().save()


class SemesterSerializer(serializers.ModelSerializer):
    pretty = serializers.SerializerMethodField()

    class Meta:
        model = Semester
        fields = ("id", "year", "term", "pretty")

    def get_pretty(self, obj):
        return str(obj)


class CourseSerializer(serializers.ModelSerializer):
    semester_pretty = serializers.StringRelatedField(source="semester")
    is_member = serializers.BooleanField(default=False, read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "course_code",
            "department",
            "course_title",
            "description",
            "semester",
            "semester_pretty",
            "archived",
            "invite_only",
            "video_chat_enabled",
            "require_video_chat_url_on_questions",
            "is_member",
        )


class CourseCreateSerializer(serializers.ModelSerializer):
    created_role = serializers.CharField(write_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "course_code",
            "department",
            "course_title",
            "description",
            "semester",
            "archived",
            "invite_only",
            "video_chat_enabled",
            "require_video_chat_url_on_questions",
            "created_role",
        )

    def create(self, validated_data):
        kind = validated_data.pop("created_role")
        instance = super().create(validated_data)
        Membership.objects.create(course=instance, user=self.context["request"].user, kind=kind)
        return instance


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email", "username")


class MembershipSerializer(CourseRouteMixin):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ("id", "kind", "time_created", "last_active", "user")

    def create(self, validated_data):
        ModelClass = self.Meta.model
        validated_data["user"] = self.context["request"].user
        validated_data["kind"] = Membership.KIND_STUDENT
        return ModelClass._default_manager.create(**validated_data)


class MembershipInviteSerializer(CourseRouteMixin):
    class Meta:
        model = MembershipInvite
        fields = ("id", "email", "kind", "time_created")


class QueueSerializer(CourseRouteMixin):
    questions_active = serializers.IntegerField(default=0, read_only=True)
    questions_asked = serializers.IntegerField(default=0, read_only=True)
    staff_active = serializers.IntegerField(default=0, read_only=True)

    class Meta:
        model = Queue
        fields = (
            "id",
            "name",
            "description",
            "archived",
            "estimated_wait_time",
            "active",
            "questions_active",
            "questions_asked",
            "staff_active",
        )
        read_only_fields = ("estimated_wait_time",)

    def update(self, instance, validated_data):
        """
        Head TAs+ can modify a queue
        TAs can only modify if a queue is active.
        """

        user = self.context["request"].user
        membership = Membership.objects.get(course=instance.course, user=user)

        if membership.is_leadership:  # User is a Head TA+
            return super().update(instance, validated_data)
        else:  # User is a TA
            if "active" in validated_data:
                instance.active = validated_data["active"]

        instance.save()
        return instance


class QuestionSerializer(QueueRouteMixin):
    asked_by = UserSerializer(read_only=True)
    responded_to_by = UserSerializer(read_only=True)

    class Meta:
        model = Question
        fields = (
            "id",
            "text",
            "video_chat_url",
            "status",
            "time_asked",
            "asked_by",
            "time_response_started",
            "time_responded_to",
            "responded_to_by",
            "rejected_reason",
            "should_send_up_soon_notification",
        )
        read_only_fields = (
            "time_asked",
            "asked_by",
            "time_response_started",
            "time_responded_to",
            "responded_to_by",
            "should_send_up_soon_notification",
        )

    def update(self, instance, validated_data):
        """
        Students can update their question's text and video_chat_url or withdraw the question
        TAs+ can only modify the status of a question.
        """
        user = self.context["request"].user
        membership = Membership.objects.get(course=instance.queue.course, user=user)

        if membership.is_ta:  # User is a TA+
            if "status" in validated_data:
                status = validated_data["status"]
                if status == Question.STATUS_WITHDRAWN:
                    raise serializers.ValidationError(
                        detail={"detail": "TAs can't mark a question as withdrawn"}
                    )
                instance.status = status
                if status == Question.STATUS_ACTIVE:
                    instance.responded_to_by = user
                    instance.time_response_started = timezone.now()
                elif status == Question.STATUS_REJECTED:
                    instance.responded_to_by = user
                    instance.time_responded_to = timezone.now()
                    instance.rejected_reason = validated_data["rejected_reason"]
                elif status == Question.STATUS_ANSWERED:
                    instance.time_responded_to = timezone.now()
                elif status == Question.STATUS_ASKED:
                    instance.responded_to_by = None
                    instance.time_response_started = None
        else:  # User is a student
            if "status" in validated_data:
                status = validated_data["status"]
                if status == Question.STATUS_WITHDRAWN:
                    instance.status = status
                else:
                    raise serializers.ValidationError(
                        detail={"detail": "Students can only withdraw a question"}
                    )
            if "text" in validated_data:
                instance.text = validated_data["text"]
            if "video_chat_url" in validated_data:
                instance.video_chat_url = validated_data["video_chat_url"]

        instance.save()
        return instance

    def create(self, validated_data):
        validated_data["status"] = Question.STATUS_ASKED
        validated_data["asked_by"] = self.context["request"].user
        return super().create(validated_data)


class MembershipPrivateSerializer(CourseRouteMixin):
    """
    Private serializer that contains course information
    """

    course = CourseSerializer(read_only=True)

    class Meta:
        model = Membership
        fields = ("id", "course", "kind", "time_created", "last_active")


class ProfileSerializer(serializers.ModelSerializer):
    phone_number = PhoneNumberField()

    class Meta:
        model = Profile
        fields = (
            "sms_notifications_enabled",
            "sms_verified",
            "sms_verification_code",
            "phone_number",
        )
        extra_kwargs = {"sms_verification_code": {"write_only": True}}


class UserPrivateSerializer(serializers.ModelSerializer):
    """
    Private serializer to allow users to see/modify their profiles.
    """

    profile = ProfileSerializer(read_only=False, required=False)
    membership_set = MembershipPrivateSerializer(many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = ("id", "first_name", "last_name", "email", "username", "profile", "membership_set")

    def update(self, instance, validated_data):
        if "profile" in validated_data:
            profile_fields = validated_data.pop("profile")
            profile = instance.profile
            # Set sms notifications enabled
            if "sms_notifications_enabled" in profile_fields:
                profile.sms_notifications_enabled = profile_fields["sms_notifications_enabled"]

            # Handle new phone number
            if (
                "phone_number" in profile_fields
                and profile_fields["phone_number"] != profile.phone_number
            ):
                profile.phone_number = profile_fields["phone_number"]
                profile.sms_verified = False
                profile.sms_verification_code = get_random_string(
                    length=6, allowed_chars="1234567890"
                )
                profile.sms_verification_timestamp = timezone.now()
                sendSMSVerification(profile.phone_number, profile.sms_verification_code)

            # Handle SMS verification
            if "sms_verification_code" in profile_fields:
                elapsed_time = timezone.now() - profile.sms_verification_timestamp
                if (
                    profile_fields["sms_verification_code"] == profile.sms_verification_code
                    and elapsed_time.total_seconds()
                    < Profile.SMS_VERIFICATION_EXPIRATION_MINUTES * 60
                ):
                    profile.sms_verified = True
                elif (
                    elapsed_time.total_seconds() >= Profile.SMS_VERIFICATION_EXPIRATION_MINUTES * 60
                ):
                    raise serializers.ValidationError(
                        detail={"detail": "Verification code has expired"}
                    )
                else:
                    raise serializers.ValidationError(
                        detail={"detail": "Incorrect verification code"}
                    )

            profile.save()
        return super().update(instance, validated_data)