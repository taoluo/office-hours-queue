from graphql_relay.node.node import from_global_id

from django.db import transaction

from ohq.apps.api.schema.types import *
from ohq.apps.api.util.errors import *
from ohq.apps.api.util.sendgrid import send_invitation_email


class CreateCourseInput(graphene.InputObjectType):
    course_code = graphene.String(required=True)
    department = graphene.String(required=True)
    course_title = graphene.String(require=True)
    description = graphene.String(required=False)
    year = graphene.Int(required=True)
    semester = graphene.Field(SemesterType, required=True)
    invite_only = graphene.Boolean(required=True)
    course_user_kind = graphene.Field(CourseUserKindType, required=False)


class CreateCourseResponse(graphene.ObjectType):
    course = graphene.Field(CourseNode, required=False)
    course_user = graphene.Field(CourseUserNode, required=False)


class CreateCourse(graphene.Mutation):
    class Arguments:
        input = CreateCourseInput(required=True)

    Output = CreateCourseResponse

    @staticmethod
    def mutate(root, info, input):
        if (
            not input.course_code or
            not input.department or
            not input.course_title
        ):
            raise empty_string_error
        with transaction.atomic():
            user = info.context.user.get_user()
            course_title = input.course_title[0].upper() + input.course_title[1:]
            course = Course.objects.create(
                course_code=input.course_code,
                department=input.department.upper(),
                course_title=course_title,
                description=input.description or "",
                year=input.year,
                semester=input.semester,
                invite_only=input.invite_only,
            )
            course_user = CourseUser.objects.create(
                user=user,
                course=course,
                kind=input.course_user_kind or CourseUserKind.PROFESSOR.name,
            )

        return CreateCourseResponse(course=course, course_user=course_user)


class UpdateCourseInput(graphene.InputObjectType):
    course_id = graphene.ID(required=True)
    course_code = graphene.String(required=False)
    department = graphene.String(required=False)
    course_title = graphene.String(required=False)
    year = graphene.Int(required=False)
    semester = graphene.Field(SemesterType, required=False)
    invite_only = graphene.Boolean(required=False)
    archived = graphene.Boolean(required=False)


class UpdateCourseResponse(graphene.ObjectType):
    course = graphene.Field(CourseNode, required=True)


class UpdateCourse(graphene.Mutation):
    class Arguments:
        input = UpdateCourseInput(required=True)

    Output = UpdateCourseResponse

    @staticmethod
    def mutate(root, info, input):
        if not input:
            raise empty_update_error
        if (
            (input.course_code is not None and not input.course_code) or
            (input.department is not None and not input.department) or
            (input.department is not None and not input.course_title)
        ):
            raise empty_string_error
        with transaction.atomic():
            user = info.context.user.get_user()
            course = Course.objects.get(pk=from_global_id(input.course_id)[1])
            if not CourseUser.objects.filter(
                user=user,
                course=course,
                kind__in=CourseUserKind.leadership(),
            ).exists():
                raise user_not_leadership_error
            if course.archived:
                raise course_archived_error
            if input.course_code is not None:
                course.course_code = input.course_code
            if input.department is not None:
                course.department = input.department.upper()
            if input.course_title is not None:
                course.course_title = input.course_title[0].upper() + input.course_title[1:]
            if input.year is not None:
                course.year = input.year
            if input.semester is not None:
                course.semester = input.semester
            if input.invite_only is not None:
                course.invite_only = input.invite_only
            if input.archived is not None:
                course.archived = input.archived
            course.save()
        return UpdateCourseResponse(course=course)


class AddUserToCourseInput(graphene.InputObjectType):
    course_id = graphene.ID(required=True)
    user_id = graphene.ID(required=True)
    kind = graphene.Field(CourseUserKindType, required=True)


class AddUserToCourseResponse(graphene.ObjectType):
    course_user = graphene.Field(CourseUserNode, required=False)


class AddUserToCourse(graphene.Mutation):
    class Arguments:
        input = AddUserToCourseInput(required=True)

    Output = AddUserToCourseResponse

    @staticmethod
    def mutate(root, info, input):
        with transaction.atomic():
            user = info.context.user.get_user()
            course = Course.objects.get(pk=from_global_id(input.course_id)[1])
            if not CourseUser.objects.filter(
                user=user,
                course=course,
                kind__in=CourseUserKind.leadership(),
            ).exists():
                raise user_not_leadership_error

            course_user = CourseUser.objects.create(
                user=User.objects.get(pk=from_global_id(input.user_id)[1]),
                course=course,
                kind=input.kind,
                invited_by=user,
            )

        return AddUserToCourseResponse(course_user=course_user)


class JoinCourseInput(graphene.InputObjectType):
    course_id = graphene.ID(required=True)


class JoinCourseResponse(graphene.ObjectType):
    course_user = graphene.Field(CourseUserNode, required=False)


class JoinCourse(graphene.Mutation):
    class Arguments:
        input = JoinCourseInput(required=True)

    Output = JoinCourseResponse

    @staticmethod
    def mutate(root, info, input):
        with transaction.atomic():
            course = Course.objects.get(pk=from_global_id(input.course_id)[1])
            if course.invite_only:
                raise course_invite_only_error
            if course.archived:
                raise course_archived_error

            course_user = CourseUser.objects.create(
                user=info.context.user.get_user(),
                course=course,
                kind=CourseUserKind.STUDENT.name,
            )

        return JoinCourseResponse(course_user=course_user)


class InviteEmailsInput(graphene.InputObjectType):
    course_id = graphene.ID(required=True)
    emails = graphene.List(graphene.String, required=True)
    kind = graphene.Field(CourseUserKindType, required=True)


class InviteEmailsResponse(graphene.ObjectType):
    invited_course_users = graphene.List(InvitedCourseUserNode, required=False)


class InviteEmails(graphene.Mutation):
    class Arguments:
        input = InviteEmailsInput(required=True)

    Output = InviteEmailsResponse

    @staticmethod
    def mutate(root, info, input):
        with transaction.atomic():
            user = info.context.user.get_user()
            course = Course.objects.get(pk=from_global_id(input.course_id)[1])
            if not CourseUser.objects.filter(
                user=user,
                course=course,
                kind__in=CourseUserKind.leadership(),
            ).exists():
                raise user_not_leadership_error
            if CourseUser.objects.filter(
                user__email__in=input.emails,
                course=course,
            ):
                raise user_in_course_error
            invited_course_users = [
                InvitedCourseUser(
                    email=email,
                    course=course,
                    invited_by=user,
                    kind=input.kind,
                ) for email in input.emails
            ]
            InvitedCourseUser.objects.bulk_create(invited_course_users)
        for invited_course_user in invited_course_users:
            send_invitation_email(invited_course_user)
        return InviteEmailsResponse(invited_course_users=invited_course_users)


class RemoveUserFromCourseInput(graphene.InputObjectType):
    course_user_id = graphene.ID(required=True)


class RemoveUserFromCourseResponse(graphene.ObjectType):
    success = graphene.Boolean(required=True)


class RemoveUserFromCourse(graphene.Mutation):
    class Arguments:
        input = RemoveUserFromCourseInput(required=True)

    Output = RemoveUserFromCourseResponse

    @staticmethod
    def mutate(root, info, input):
        with transaction.atomic():
            course_user_to_remove = CourseUser.objects.get(
                pk=from_global_id(input.course_user_id)[1],
            )
            if not CourseUser.objects.filter(
                user= info.context.user.get_user(),
                course=course_user_to_remove.course,
                kind__in=CourseUserKind.leadership(),
            ).exists():
                raise user_not_leadership_error

            # Prevent removal of last leadership user
            if (
                course_user_to_remove.kind in CourseUserKind.leadership() and
                CourseUser.objects.filter(
                    course=course_user_to_remove.course,
                    kind__in=CourseUserKind.leadership()
                ).count() == 1
            ):
                raise remove_only_leadership_error

            course_user_to_remove.delete()

        return RemoveUserFromCourseResponse(success=True)


class RemoveInvitedUserFromCourseInput(graphene.InputObjectType):
    invited_course_user_id = graphene.ID(required=True)


class RemoveInvitedUserFromCourseResponse(graphene.ObjectType):
    success = graphene.Boolean(required=True)


class RemoveInvitedUserFromCourse(graphene.Mutation):
    class Arguments:
        input = RemoveInvitedUserFromCourseInput(required=True)

    Output = RemoveInvitedUserFromCourseResponse

    @staticmethod
    def mutate(root, info, input):
        with transaction.atomic():
            invited_course_user_to_remove = InvitedCourseUser.objects.get(
                pk=from_global_id(input.invited_course_user_id)[1],
            )
            if not CourseUser.objects.filter(
                user= info.context.user.get_user(),
                course=invited_course_user_to_remove.course,
                kind__in=CourseUserKind.leadership(),
            ).exists():
                raise user_not_leadership_error
            invited_course_user_to_remove.delete()
        return RemoveInvitedUserFromCourseResponse(success=True)


class ResendInviteEmailInput(graphene.InputObjectType):
    invited_course_user_id = graphene.ID(required=True)


class ResendInviteEmailResponse(graphene.ObjectType):
    success = graphene.Boolean(required=True)


class ResendInviteEmail(graphene.Mutation):
    class Arguments:
        input = ResendInviteEmailInput(required=True)

    Output = ResendInviteEmailResponse

    @staticmethod
    def mutate(root, info, input):
        with transaction.atomic():
            user = info.context.user.get_user()
            invited_course_user = InvitedCourseUser.objects.get(
                pk=from_global_id(input.invited_course_user_id)[1],
            )
            if not CourseUser.objects.filter(
                user=user,
                course=invited_course_user,
                kind__in=CourseUserKind.leadership(),
            ).exists():
                raise user_not_leadership_error

        send_invitation_email(invited_course_user)
        return ResendInviteEmailResponse(success=True)
