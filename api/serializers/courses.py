import random
from rest_framework import serializers
from django.db import transaction
from django.utils import timezone
from api.serializers.media import MediaSerializer
from api.serializers.users import BasicUserInfoSerializer, UserListSerializer
from core.models.courses import (
    CoursePathWay,
    Course,
    CourseProject,
    CourseRating,
    LessonRating,
    Module,
    Assignment,
    Lesson,
    LessonQuiz,
    LessonQuizOption,
    LessonQuizScore,
    ModuleAssignmentResponse,
    CourseProjectResponse,
    QouteToken,
    Qoutes,
    CourseEnrollment,
    Badge,
    UserBadge,
    Certificate,
    PortfolioContent,
    Flashcard,
    Library,
    DiscountCode,
)
from core.models.users import AssignedClass
from core.models.users import User


# CoursePathWay Serializers
class CoursePathWaySerializer(serializers.ModelSerializer):
    """Serializer for creating CoursePathWay"""

    class Meta:
        model = CoursePathWay
        fields = ["title", "description", "cover_image"]


class ReturnCoursePathWaySerializer(serializers.ModelSerializer):
    """Serializer for returning CoursePathWay data"""

    cover_image = MediaSerializer()

    class Meta:
        model = CoursePathWay
        fields = [
            "id",
            "title",
            "description",
            "cover_image",
            "created_at",
            "updated_at",
        ]


# Course Serializers
class CourseSerializer(serializers.ModelSerializer):
    """Serializer for creating Course"""

    class Meta:
        model = Course
        fields = [
            "title",
            "description",
            "instructor",
            "cover_image",
            "level",
            "stage",
            "course_pathway",
            "amount",
            "badge_icon",
        ]


class ReturnCourseSerializerFrankOnly(serializers.ModelSerializer):
    """Serializer for returning Course data"""

    cover_image = MediaSerializer()
    course_pathway = ReturnCoursePathWaySerializer()
    instructor = BasicUserInfoSerializer()
    badge_icon = MediaSerializer()
    step_number = serializers.SerializerMethodField()
    modules = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "instructor",
            "cover_image",
            "level",
            "stage",
            "course_pathway",
            "amount",
            "modules",
            "step_number",
            "badge_icon",
            "created_at",
            "updated_at",
        ]

    def get_step_number(self, obj):
        return random.randint(1, 100)

    def get_modules(self, obj):
        modules = Module.objects.filter(course=obj)
        serializer = ReturnModuleSerializer(modules, many=True)
        return serializer.data


class ReturnCourseSerializer(serializers.ModelSerializer):
    """Serializer for returning Course data"""

    cover_image = MediaSerializer()
    course_pathway = ReturnCoursePathWaySerializer()
    instructor = BasicUserInfoSerializer()
    badge_icon = MediaSerializer()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "instructor",
            "cover_image",
            "level",
            "stage",
            "course_pathway",
            "amount",
            "badge_icon",
            "created_at",
            "updated_at",
        ]


class EnrolledCourseSerializer(serializers.ModelSerializer):
    """Serializer for returning Course data"""

    cover_image = MediaSerializer()
    course_pathway = ReturnCoursePathWaySerializer()
    instructor = BasicUserInfoSerializer()
    user_current_course_module_and_lesson = serializers.SerializerMethodField()
    user_course_progress = serializers.SerializerMethodField()
    course_lesson_count = serializers.SerializerMethodField()
    course_module_count = serializers.SerializerMethodField()
    badge_icon = MediaSerializer()

    class Meta:
        model = Course
        fields = [
            "id",
            "title",
            "description",
            "instructor",
            "cover_image",
            "level",
            "stage",
            "course_pathway",
            "amount",
            "badge_icon",
            "created_at",
            "updated_at",
            "user_current_course_module_and_lesson",
            "user_course_progress",
            "course_lesson_count",
            "course_module_count",
        ]

    def get_user_current_course_module_and_lesson(self, obj):
        user = self.context.get("request").user
        return obj.user_current_course_module_and_lesson(user)

    def get_user_course_progress(self, obj):
        user = self.context.get("request").user
        return obj.user_course_progress(user)

    def get_course_module_count(self, obj):
        return obj.course_module_count()

    def get_course_lesson_count(self, obj):
        return obj.course_lesson_count()


# CourseProject Serializers
class CourseProjectSerializer(serializers.ModelSerializer):
    """Serializer for creating CourseProject"""

    class Meta:
        model = CourseProject
        fields = [
            "title",
            "description",
            "course",
            "transcript",
            "video_embed",
            "grading_description",
            "is_locked",
        ]


class ReturnCourseProjectSerializer(serializers.ModelSerializer):
    """Serializer for returning CourseProject data"""

    course = ReturnCourseSerializer()

    class Meta:
        model = CourseProject
        fields = [
            "id",
            "title",
            "description",
            "course",
            "transcript",
            "video_embed",
            "grading_description",
            "is_locked",
            "created_at",
            "updated_at",
        ]


# Module Serializers
class ModuleSerializer(serializers.ModelSerializer):
    """Serializer for creating Module"""

    class Meta:
        model = Module
        fields = [
            "title",
            "description",
            "cover_image",
            "course",
            "learning_outcome",
            "objectives",
            "order",
            "badge_icon",
        ]

    def validate(self, attrs):
        """check if a module with this order already exists, also get all the existing orders
        and make the user know the existing order"""
        course_id = attrs["course"].id
        order = attrs["order"]
        existing_orders = list(
            Module.objects.filter(course_id=course_id).values_list("order", flat=True)
        )

        if Module.objects.filter(course_id=course_id, order=order).exists():
            raise serializers.ValidationError(
                f"These order number already exists {existing_orders} "
            )

        return super().validate(attrs)


class UpdateModuleSerializer(serializers.ModelSerializer):
    """Serializer for creating Module"""

    class Meta:
        model = Module
        fields = [
            "title",
            "description",
            "cover_image",
            "course",
            "learning_outcome",
            "objectives",
            "order",
            "badge_icon",
        ]

    def validate(self, attrs):
        """check if a module with this order already exists, also get all the existing orders
        and make the user know the existing order"""
        order = attrs.get("order", None)
        course = attrs.get("course", None)

        if order:
            if not course and self.instance:
                # If course is not in attrs but we're updating, use the instance's course
                course_id = self.instance.course.id
            elif course:
                course_id = course.id
            else:
                raise serializers.ValidationError(
                    "Course is required when setting order"
                )

            # Exclude current instance when updating
            queryset = Module.objects.filter(course_id=course_id)
            if self.instance:
                queryset = queryset.exclude(id=self.instance.id)

            existing_orders = list(queryset.values_list("order", flat=True))

            if queryset.filter(order=order).exists():
                raise serializers.ValidationError(
                    f"These order numbers already exist: {existing_orders}. Please choose a different order."
                )
        return super().validate(attrs)


class ReturnModuleSerializer(serializers.ModelSerializer):
    """Serializer for returning Module data"""

    cover_image = MediaSerializer()
    course = ReturnCourseSerializer()
    badge_icon = MediaSerializer()

    class Meta:
        model = Module
        fields = [
            "id",
            "title",
            "description",
            "cover_image",
            "course",
            "badge_icon",
            "learning_outcome",
            "objectives",
            "created_at",
            "updated_at",
            "order",
        ]


class DetailedReturnModuleSerializerJames(serializers.ModelSerializer):
    """Serializer for returning Module data"""

    cover_image = MediaSerializer()
    course = ReturnCourseSerializer()
    badge_icon = MediaSerializer()
    module_flashcards = serializers.SerializerMethodField()
    module_assignments = serializers.SerializerMethodField()
    module_lessons = serializers.SerializerMethodField()
    has_submitted_assignment = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = [
            "id",
            "title",
            "description",
            "cover_image",
            "course",
            "badge_icon",
            "order",
            "learning_outcome",
            "objectives",
            "created_at",
            "updated_at",
            "module_flashcards",
            "module_assignments",
            "module_lessons",
            "has_submitted_assignment",
        ]

    def get_module_flashcards(self, obj):
        flashcards = Flashcard.objects.filter(module=obj)
        serializer = ReturnFlashcardSerializer(flashcards, many=True)
        return serializer.data

    def get_module_assignments(self, obj):
        assignments = Assignment.objects.filter(module=obj)
        serializer = ReturnAssignmentSerializer(assignments, many=True)
        return serializer.data

    def get_module_lessons(self, obj):
        lessons = Lesson.objects.filter(module=obj)
        request = self.context.get("request")
        serializer = DetailedReturnLessonSerializerJames(
            lessons, many=True, context={"request": request}
        )
        return serializer.data

    def get_has_submitted_assignment(self, obj):
        user = self.context.get("request").user
        return obj.has_submitted_assignment(user)


class MreDetailedReturnModuleSerializer(serializers.ModelSerializer):
    """Serializer for returning Module data"""

    cover_image = MediaSerializer()
    course = ReturnCourseSerializer()
    badge_icon = MediaSerializer()
    module_flashcards = serializers.SerializerMethodField()
    module_assignments = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = [
            "id",
            "title",
            "module_flashcards",
            "module_assignments",
            "description",
            "cover_image",
            "course",
            "badge_icon",
            "learning_outcome",
            "objectives",
            "order",
            "created_at",
            "updated_at",
        ]

    def get_module_flashcards(self, obj):
        flashcards = Flashcard.objects.filter(module=obj)
        serializer = ReturnFlashcardSerializer(flashcards, many=True)
        return serializer.data

    def get_module_assignments(self, obj):
        assignments = Assignment.objects.filter(module=obj)
        serializer = ReturnAssignmentSerializer(assignments, many=True)
        return serializer.data


class EnrolledModuleSerializer(serializers.ModelSerializer):
    """Serializer for returning Module data"""

    cover_image = MediaSerializer()
    course = ReturnCourseSerializer()
    module_progress_percentage = serializers.SerializerMethodField()
    badge_icon = MediaSerializer()
    is_unlocked_for_user = serializers.SerializerMethodField()
    has_submitted_assignment = serializers.SerializerMethodField()

    class Meta:
        model = Module
        fields = [
            "id",
            "title",
            "description",
            "cover_image",
            "course",
            "order",
            "learning_outcome",
            "objectives",
            "badge_icon",
            "created_at",
            "updated_at",
            "total_lessons",
            "total_quizzes",
            "total_assignments",
            "module_progress_percentage",
            "is_unlocked_for_user",
            "has_submitted_assignment",
        ]

    def get_module_progress_percentage(self, obj):
        user = self.context.get("request").user
        return obj.module_progress_percentage(user)

    def get_has_submitted_assignment(self, obj):
        user = self.context.get("request").user
        return obj.has_submitted_assignment(user)

    def get_is_unlocked_for_user(self, obj):
        user = self.context.get("request").user
        return obj.is_unlocked_for_user(user)


# Assignment Serializers
class AssignmentSerializer(serializers.ModelSerializer):
    """Serializer for creating Assignment"""

    class Meta:
        model = Assignment
        fields = ["title", "description", "module", "grading_description", "is_locked"]


class ReturnAssignmentSerializer(serializers.ModelSerializer):
    """Serializer for returning Assignment data"""

    module = ReturnModuleSerializer()

    class Meta:
        model = Assignment
        fields = [
            "id",
            "title",
            "description",
            "module",
            "grading_description",
            "is_locked",
            "created_at",
            "updated_at",
        ]


# Lesson Serializers
class LessonSerializer(serializers.ModelSerializer):
    """Serializer for creating Lesson"""

    class Meta:
        model = Lesson
        fields = [
            "title",
            "description",
            "cover_image",
            "module",
            "transcript",
            "note",
            "video_embed",
            "order",
            # "is_locked",
        ]

    def validate(self, attrs):
        """check if a lesson with this order already exists, also get all the existing orders
        and make the user know the existing order"""
        module_id = attrs["module"].id
        order = attrs["order"]
        existing_orders = list(
            Lesson.objects.filter(module_id=module_id).values_list("order", flat=True)
        )

        if Lesson.objects.filter(module_id=module_id, order=order).exists():
            raise serializers.ValidationError(
                f"These order number already exists {existing_orders} "
            )

        return super().validate(attrs)


class UpdateLessonSerializer(serializers.ModelSerializer):
    """Serializer for creating Lesson"""

    class Meta:
        model = Lesson
        fields = [
            "title",
            "description",
            "cover_image",
            "module",
            "transcript",
            "note",
            "video_embed",
            "order",
            # "is_locked",
        ]

    def validate(self, attrs):
        """check if a lesson with this order already exists, also get all the existing orders
        and make the user know the existing order"""
        order = attrs.get("order", None)
        if order:
            try:
                module_id = attrs["module"].id
            except KeyError as ke:
                raise serializers.ValidationError(f"Missing required field: {ke}")
            existing_orders = list(
                Lesson.objects.filter(module_id=module_id).values_list(
                    "order", flat=True
                )
            )

            if Lesson.objects.filter(module_id=module_id, order=order).exists():
                raise serializers.ValidationError(
                    f"These order number already exists {existing_orders} "
                )
        return super().validate(attrs)


class DetailedReturnLessonSerializerJames(serializers.ModelSerializer):
    """Serializer for returning Lesson data"""

    cover_image = MediaSerializer()
    is_unlocked_for_user = serializers.SerializerMethodField()
    lesson_quizes = serializers.SerializerMethodField()
    has_completed_lesson = serializers.SerializerMethodField()
    has_taken_quiz = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "description",
            "cover_image",
            "module",
            "transcript",
            "lesson_quizes",
            "note",
            "video_embed",
            "order",
            # "is_locked",
            "created_at",
            "updated_at",
            "is_unlocked_for_user",
            "has_completed_lesson",
            "has_taken_quiz",
        ]

    def get_is_unlocked_for_user(self, obj):
        user = self.context.get("request").user
        return obj.is_unlocked_for_user(user)

    def get_has_completed_lesson(self, obj):
        user = self.context.get("request").user
        return obj.has_completed_lesson(user)

    def get_lesson_quizes(self, obj):
        lesson_quizes = LessonQuiz.objects.filter(lesson=obj)
        print(lesson_quizes, "bfsdfvbdsvb")
        serializer = LessonQuizSerializer(lesson_quizes, many=True)
        return serializer.data

    def get_has_taken_quiz(self, obj):
        user = self.context.get("request").user
        return obj.has_taken_quiz(user)


class ReturnLessonSerializer(serializers.ModelSerializer):
    """Serializer for returning Lesson data"""

    cover_image = MediaSerializer()
    module = MreDetailedReturnModuleSerializer()
    is_unlocked_for_user = serializers.SerializerMethodField()
    lesson_quizes = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id",
            "title",
            "description",
            "cover_image",
            "module",
            "transcript",
            "lesson_quizes",
            "note",
            "video_embed",
            "order",
            # "is_locked",
            "created_at",
            "updated_at",
            "is_unlocked_for_user",
        ]

    def get_is_unlocked_for_user(self, obj):
        user = self.context.get("request").user
        return obj.is_unlocked_for_user(user)

    def get_lesson_quizes(self, obj):
        lesson_quizes = LessonQuiz.objects.filter(lesson=obj)
        print(lesson_quizes, "bfsdfvbdsvb")
        serializer = LessonQuizSerializer(lesson_quizes, many=True)
        return serializer.data


# LessonQuizScore Serializers
class LessonQuizScoreSerializer(serializers.Serializer):
    """Serializer for creating LessonQuizScore"""

    lesson = serializers.CharField()
    score = serializers.IntegerField()
    time_spent = serializers.FloatField()


class ReturnLessonQuizScoreSerializer(serializers.ModelSerializer):
    """Serializer for returning LessonQuizScore data"""

    lesson = ReturnLessonSerializer()
    user = BasicUserInfoSerializer()

    class Meta:
        model = LessonQuizScore
        fields = ["id", "lesson", "user", "score", "created_at", "updated_at"]


# ModuleAssignmentResponse Serializers
class ModuleAssignmentResponseSerializer(serializers.ModelSerializer):
    """Serializer for creating ModuleAssignmentResponse"""

    class Meta:
        model = ModuleAssignmentResponse
        fields = ["assignment", "response", "attachment", "score", "feedback"]


class ReturnModuleAssignmentResponseSerializer(serializers.ModelSerializer):
    """Serializer for returning ModuleAssignmentResponse data"""

    assignment = ReturnAssignmentSerializer()
    user = BasicUserInfoSerializer()
    attachment = MediaSerializer()

    class Meta:
        model = ModuleAssignmentResponse
        fields = [
            "id",
            "assignment",
            "user",
            "response",
            "attachment",
            "feedback",
            "score",
            "created_at",
            "updated_at",
        ]


# CourseProjectResponse Serializers
class CourseProjectResponseSerializer(serializers.ModelSerializer):
    """Serializer for creating CourseProjectResponse"""

    class Meta:
        model = CourseProjectResponse
        fields = [
            "project",
            "response",
            "attachment",
            "score",
            "feedback",
        ]

    def validate(self, attrs):
        # check if the user has submitted a project before
        project = attrs.get("project")
        user = self.context.get("request").user
        if CourseProjectResponse.objects.filter(project=project, user=user).exists():
            raise serializers.ValidationError(
                "You already submitted, cannot submit twice."
            )

        return super().validate(attrs)


class ReturnCourseProjectResponseSerializer(serializers.ModelSerializer):
    """Serializer for returning CourseProjectResponse data"""

    project = ReturnCourseProjectSerializer()
    user = BasicUserInfoSerializer()
    attachment = MediaSerializer()

    class Meta:
        model = CourseProjectResponse
        fields = [
            "id",
            "project",
            "user",
            "response",
            "feedback",
            "attachment",
            "score",
            "created_at",
            "updated_at",
        ]


class LessonQuizOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = LessonQuizOption
        fields = ["id", "text_option", "option_label", "image_option"]


class LessonQuizSerializer(serializers.ModelSerializer):
    options = LessonQuizOptionSerializer(
        source="lessonquizoption_set", many=True, required=False
    )

    class Meta:
        model = LessonQuiz
        fields = ["id", "type", "question", "lesson", "correct_answer", "options"]

    def create(self, validated_data):
        options_data = validated_data.pop("lessonquizoption_set", [])

        with transaction.atomic():
            quiz = LessonQuiz.objects.create(**validated_data)
            for option_data in options_data:
                LessonQuizOption.objects.create(lesson_quiz=quiz, **option_data)

        return quiz

    def update(self, instance, validated_data):
        options_data = validated_data.pop("lessonquizoption_set", [])

        # Update quiz instance
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Handle options
        with transaction.atomic():
            # Delete existing options not in the update data
            instance.lessonquizoption_set.all().delete()

            # Create new options
            for option_data in options_data:
                LessonQuizOption.objects.create(lesson_quiz=instance, **option_data)

        return instance


class LessonQuizListSerializer(serializers.Serializer):
    quizzes = LessonQuizSerializer(many=True)

    def create(self, validated_data):
        quizzes_data = validated_data.pop("quizzes", [])

        with transaction.atomic():
            quizzes = []
            for quiz_data in quizzes_data:
                options_data = quiz_data.pop("lessonquizoption_set", [])
                quiz = LessonQuiz.objects.create(**quiz_data)
                for option_data in options_data:
                    LessonQuizOption.objects.create(lesson_quiz=quiz, **option_data)
                quizzes.append(quiz)

        return {"quizzes": quizzes}

    def update(self, instance, validated_data):
        quizzes_data = validated_data.pop("quizzes", [])

        with transaction.atomic():
            # Delete all existing quizzes and options
            LessonQuiz.objects.filter(lesson=instance["lesson"]).delete()

            # Create new quizzes and options
            quizzes = []
            for quiz_data in quizzes_data:
                options_data = quiz_data.pop("lessonquizoption_set", [])
                quiz = LessonQuiz.objects.create(**quiz_data)
                for option_data in options_data:
                    LessonQuizOption.objects.create(lesson_quiz=quiz, **option_data)
                quizzes.append(quiz)

        return {"quizzes": quizzes}


class PurchaseCourseSerializer(serializers.Serializer):
    """
    Serializer to accept an array of course IDs.
    """

    courses = serializers.ListField(
        child=serializers.CharField(), help_text="List of course IDs to purchase."
    )


class CheckDiscountCodeSerializer(serializers.Serializer):
    """
    Serializer to accept an array of course IDs.
    """

    courses = serializers.ListField(
        child=serializers.CharField(), help_text="List of course IDs to purchase."
    )
    # discount_code = serializers.CharField(
    #     help_text="Discount code to apply to the purchase.",
    #     required=True,
    # )


class CreateQuoteSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new quote.
    """

    class Meta:
        model = Qoutes
        fields = [
            "term",
            "course_pathway",
            "class_name",
            "quantity",
            "term_start",
            "term_end",
            "status",
        ]


class ReturnQuoteSerializer(serializers.ModelSerializer):
    """
    Serializer for returning quote details.
    Includes user and course pathway as human-readable strings.
    """

    user = serializers.StringRelatedField()
    course_pathway = ReturnCoursePathWaySerializer()
    status_display = serializers.CharField(source="get_status_display", read_only=True)
    user = UserListSerializer()

    class Meta:
        model = Qoutes
        fields = [
            "id",
            "user",
            "quantity",
            "quantity_left",
            "course_pathway",
            "class_name",
            "term",
            "status",
            "status_display",
            "is_paused",
            "is_active",
            "term_start",
            "term_end",
            "created_at",
            "updated_at",
        ]


class BulkCreateQuoteTokenSerializer(serializers.Serializer):
    """Serializer for creating tokens for multiple users."""

    user_ids = serializers.ListField(
        child=serializers.UUIDField(), help_text="List of user UUIDs."
    )
    quote_id = serializers.CharField(help_text="ID of the related quote.")

    def validate(self, attrs):
        try:
            quote = Qoutes.objects.get(id=attrs["quote_id"])
        except Qoutes.DoesNotExist:
            raise serializers.ValidationError(
                {"quote_id": "The specified quote does not exist."}
            )
        attrs["quote"] = quote

        # check if the quote is approved
        if quote.status != "approved":
            raise serializers.ValidationError(
                {"quote_id": "The specified quote is not approved."}
            )

        # check if the quote is paused
        if quote.is_paused:
            raise serializers.ValidationError(
                {"quote_id": "The specified quote is paused."}
            )

        # check if the quote is expired
        if quote.term_end < timezone.now():
            raise serializers.ValidationError(
                {"quote_id": "The specified quote has expired."}
            )

        # check if the quote quantit left is < user count
        if quote.quantity_left < len(attrs["user_ids"]):
            raise serializers.ValidationError(
                {"quantity_left": "Not enough quantity left for the specified users."}
            )

        user_ids = attrs["user_ids"]
        existing_users = set(
            User.objects.filter(id__in=user_ids).values_list("id", flat=True)
        )

        print(len(attrs["user_ids"]))

        non_existent_users = [str(uid) for uid in user_ids if uid not in existing_users]

        if non_existent_users:
            raise serializers.ValidationError(
                {
                    "user_ids": f"The following user IDs do not exist: {', '.join(non_existent_users)}"
                }
            )

        return attrs


class UnlockCourseWithCodeSerializer(serializers.Serializer):
    """Allow the user submit their token which would be used to enroll them into courses"""

    token = serializers.CharField(max_length=6)


class CourseRatingSerializer(serializers.ModelSerializer):
    """serializer for creating course rating"""

    class Meta:
        model = CourseRating
        fields = ["course", "user", "score", "feedback_text"]


class UpdateCourseRatingSerializer(serializers.ModelSerializer):
    """serializer for creating course rating"""

    class Meta:
        model = CourseRating
        fields = ["score", "feedback_text"]


class ReturnCourseRatingSerializer(serializers.ModelSerializer):
    """serializer for returning course rating data"""

    class Meta:
        model = CourseRating
        fields = [
            "id",
            "course",
            "user",
            "score",
            "feedback_text",
            "created_at",
            "updated_at",
        ]


class LessonRatingSerializer(serializers.ModelSerializer):
    """serializer for creating lession rating"""

    class Meta:
        model = LessonRating
        fields = [
            "lesson",
            "user",
            "rating",
            "rating_status",
            "section",
            "feedback_text",
        ]


class UpdateLessonRatingSerializer(serializers.ModelSerializer):
    """serializer for updating lession rating"""

    class Meta:
        model = LessonRating
        fields = ["rating", "rating_status", "section", "feedback_text"]


class ReturnLessonRatingSerializer(serializers.ModelSerializer):
    """serializer for creating lession rating"""

    class Meta:
        model = LessonRating
        fields = [
            "id",
            "lesson",
            "user",
            "rating",
            "rating_status",
            "section",
            "feedback_text",
            "created_at",
            "updated_at",
        ]


class ReportCardSerilaizer(serializers.Serializer):
    """serializer for creating report card"""

    user = serializers.UUIDField()
    course = serializers.UUIDField()

    def validate(self, attrs):
        try:
            user = User.objects.get(id=attrs["user"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"user": "User not found"})

        try:
            course = Course.objects.get(id=attrs["course"])
        except Course.DoesNotExist:
            raise serializers.ValidationError({"course": "Course not found"})

        # check if the user is enrolled in that class
        try:
            CourseEnrollment.objects.get(user=user, course=course)
        except CourseEnrollment.DoesNotExist:
            raise serializers.ValidationError(
                {"course": "User is not enrolled in this course."}
            )
        attrs["course"] = course
        attrs["user"] = user
        return super().validate(attrs)


class BadgeSerializer(serializers.ModelSerializer):
    """badge serializer"""

    icon = MediaSerializer()

    class Meta:
        model = Badge
        fields = [
            "id",
            "name",
            "description",
            "icon",
            "created_at",
            "updated_at",
        ]


class UserBadgeSerializer(serializers.ModelSerializer):
    """badge serializer"""

    badge = BadgeSerializer()

    class Meta:
        model = UserBadge
        fields = [
            "id",
            "user",
            "badge",
            "earned_date",
            "created_at",
            "updated_at",
        ]


class VideoEmbedSerializer(serializers.ModelSerializer):
    """video embed serializer"""

    class Meta:
        model = Lesson
        fields = [
            "video_embed",
        ]


class CertificateSerializer(serializers.ModelSerializer):
    """user certificates"""

    certificate_file = MediaSerializer()

    class Meta:
        model = Certificate
        fields = [
            "id",
            "course",
            "user",
            "certificate_file",
            "created_at",
            "updated_at",
        ]


class PortfolioContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PortfolioContent
        fields = [
            "id",
            "user",
            "title",
            "description",
            "content_type",
            "date",
            "link",
            "team_members",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at", "user"]

    def create(self, validated_data):
        # Automatically set the user to the current authenticated user
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)


class ReturnAssignedClassSerializer(serializers.ModelSerializer):
    """serializer to get a teacher's class"""

    class Meta:
        model = AssignedClass
        fields = "__all__"


class FlashcardSerializer(serializers.ModelSerializer):
    """Serializer for Flashcard model"""

    class Meta:
        model = Flashcard
        fields = ["id", "module", "question", "answer", "created_at", "updated_at"]


class ReturnFlashcardSerializer(serializers.ModelSerializer):
    """Serializer for returning Flashcard data with module details"""

    module = ReturnModuleSerializer()

    class Meta:
        model = Flashcard
        fields = ["id", "module", "question", "answer", "created_at", "updated_at"]


class LibrarySerializer(serializers.ModelSerializer):
    """Serializer for creating and updating Library content"""

    class Meta:
        model = Library
        fields = [
            "id",
            "pathway",
            "title",
            "description",
            "video_embed",
            "media",
            "library_type",
        ]
        read_only_fields = ["id", "user"]


class ReturnLibrarySerializer(serializers.ModelSerializer):
    """Serializer for returning Library content with expanded relations"""

    user = BasicUserInfoSerializer()
    pathway = ReturnCoursePathWaySerializer()
    media = MediaSerializer()

    class Meta:
        model = Library
        fields = [
            "id",
            "user",
            "pathway",
            "title",
            "description",
            "video_embed",
            "media",
            "library_type",
            "created_at",
            "updated_at",
        ]


class DiscountCodeSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating discount codes.
    """

    class Meta:
        model = DiscountCode
        fields = [
            "id",
            "courses",
            "code",
            "percentage_off",
            "start_date",
            "end_date",
            "max_uses",
            "used_count",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
