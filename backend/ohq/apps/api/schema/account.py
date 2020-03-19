from firebase_admin import auth
from django.db import transaction

from ohq.apps.api.schema.types import *
from ohq.apps.api.util.errors import empty_update_error, empty_string_error, email_not_upenn_error


class CreateUserInput(graphene.InputObjectType):
    full_name = graphene.String(required=True)
    preferred_name = graphene.String(required=True)
    phone_number = graphene.String(required=False)
    sms_notifications_enabled = graphene.Boolean(required=False)


class CreateUserResponse(graphene.ObjectType):
    user = graphene.Field(UserNode, required=True)


class CreateUser(graphene.Mutation):
    class Arguments:
        input = CreateUserInput(required=True)

    Output = CreateUserResponse

    @staticmethod
    def mutate(root, info, input):
        if (
            not input.full_name or
            not input.preferred_name
        ):
            raise empty_string_error
        if not info.context.user.email.endswith("upenn.edu"):
            raise email_not_upenn_error
        with transaction.atomic():
            auth.set_custom_user_claims(
                info.context.user.firebase_uid,
                { "hasUserObject": True },
            )
            user = User(
                full_name=input.full_name,
                preferred_name=input.preferred_name,
                email=info.context.user.email,
                phone_number=input.phone_number,
                sms_notifications_enabled=input.sms_notifications_enabled or False,
                auth_user=info.context.user,
            )
            user.clean_fields()
            invites = InvitedCourseUser.objects.filter(email=info.context.user.email)
            new_course_users = [
                CourseUser(
                    user=user,
                    course=invite.course,
                    kind=invite.kind,
                    invited_by=invite.invited_by,
                ) for invite in invites
            ]
            user.save()
            CourseUser.objects.bulk_create(new_course_users)
            invites.delete()

        return CreateUserResponse(user=user)


class UpdateUserInput(graphene.InputObjectType):
    full_name = graphene.String(required=False)
    preferred_name = graphene.String(required=False)
    phone_number = graphene.String(required=False)
    sms_notifications_enabled = graphene.Boolean(required=False)


class UpdateUserResponse(graphene.ObjectType):
    user = graphene.Field(UserNode, required=True)


class UpdateUser(graphene.Mutation):
    class Arguments:
        input = UpdateUserInput(required=True)

    Output = UpdateUserResponse

    @staticmethod
    def mutate(root, info, input):
        if not input:
            raise empty_update_error
        if (
            (input.full_name is not None and not input.full_name) or
            (input.preferred_name is not None and not input.preferred_name)
        ):
            raise empty_string_error
        with transaction.atomic():
            user = info.context.user.get_user()
            if input.full_name is not None:
                user.full_name = input.full_name
            if input.preferred_name is not None:
                user.preferred_name = input.preferred_name
            if input.phone_number is not None:
                user.phone_number = input.phone_number
            if input.sms_notifications_enabled is not None:
                user.sms_notifications_enabled = input.sms_notifications_enabled
            user.clean_fields()
            user.save()

        return UpdateUserResponse(user=user)
