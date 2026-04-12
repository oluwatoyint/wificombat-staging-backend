from django.apps import apps
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q

from .models.users import TransactionHistory, User, School, Otp, Wallet
from core.models.users import UserActivity
from core.models.media import Media
from core.models.production_tasks import ProductionTask
from core.models.courses import (
    Assignment,
    Course,
    CoursePathWay,
    CourseProject,
    CourseRating,
    Lesson,
    LessonQuiz,
    LessonQuizOption,
    LessonQuizScore,
    LessonRating,
    Module,
)


admin.site.register(Otp)
admin.site.register(Wallet)
admin.site.register(TransactionHistory)
admin.site.register(Media)
admin.site.register(UserActivity)
admin.site.register(ProductionTask)
admin.site.register(CoursePathWay)


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 0
    fields = (
        "title",
        "order",
        "is_locked",
        "video_embed",
    )
    ordering = ["order"]


class ModuleInline(admin.StackedInline):
    model = Module
    extra = 0
    fields = (
        "title",
        "description",
        "learning_outcome",
        "objectives",
        "order",
        "badge_icon",
    )
    inlines = [LessonInline]
    show_change_link = True

    def get_formset(self, request, obj=None, **kwargs):
        formset = super().get_formset(request, obj, **kwargs)
        formset.nested_inlines = [LessonInline]
        return formset


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("title", "level", "stage", "course_pathway", "amount", "instructor")
    list_filter = ("level", "stage", "course_pathway", "instructor")
    search_fields = (
        "title",
        "description",
        "instructor__email",
        "instructor__full_name",
    )
    inlines = [ModuleInline]

    class Media:
        css = {
            "all": [
                "admin/css/forms.css",
                "admin/css/widgets.css",
            ]
        }
        js = [
            "admin/js/jquery.init.js",
            "admin/js/inlines.js",
        ]

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = extra_context or {}
        extra_context["show_save_and_continue"] = True
        return super().change_view(request, object_id, form_url, extra_context)


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    inlines = [LessonInline]
    list_display = ("title", "course", "order")
    list_filter = ("course",)
    search_fields = ("title", "course__title")


admin.site.register(CourseProject)
admin.site.register(Assignment)
admin.site.register(Lesson)
admin.site.register(LessonQuiz)
admin.site.register(LessonQuizOption)
admin.site.register(LessonQuizScore)


admin.site.register(LessonRating)


@admin.register(School)
class SchoolAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at", "updated_at")
    search_fields = ("name",)
    ordering = ("-created_at",)

    def get_queryset(self, request):
        """Override queryset to optimize performance"""
        return super().get_queryset(request).select_related()


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "email",
        "full_name",
        "role",
        "school",
        "is_active",
        "profile_picture",
        "created_at",
    )
    list_filter = (
        "is_active",
        "is_staff",
        "role",
        "school",
        "created_at",
    )
    search_fields = ("email", "full_name", "phone")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (
            "Personal Info",
            {
                "fields": (
                    "full_name",
                    "phone",
                    "sex",
                    "bio",
                    "profile_pic",
                    "school",
                    "_class",
                    "fcm_token",
                )
            },
        ),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "role",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "full_name",
                    "role",
                    "is_active",
                ),
            },
        ),
    )

    def profile_picture(self, obj):
        """Display profile picture thumbnail in admin"""
        if obj.profile_pic and obj.profile_pic.media:
            return format_html(
                '<img src="{}" width="50" height="50" style="border-radius: 50%;" />',
                obj.profile_pic.media.url,
            )
        return format_html("<span>No Image</span>")

    profile_picture.short_description = "Profile Picture"

    def get_queryset(self, request):
        """Optimize queries with select_related"""
        return super().get_queryset(request).select_related("school", "profile_pic")


app_models = apps.get_app_config("core").get_models()

for model in app_models:
    try:
        admin.site.register(model)
    except admin.sites.AlreadyRegistered:
        # Skip models that are already registered
        pass
