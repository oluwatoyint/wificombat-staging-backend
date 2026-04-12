from django.urls import path, include
from rest_framework.routers import DefaultRouter
from api.controllers.course import (
    CoursePathWayViewSet,
    CourseRatingViewSet,
    CourseViewSet,
    LessonRatingViewSet,
    ModuleViewSet,
    LessonViewSet,
    AssignmentViewSet,
    CourseProjectViewSet,
    LessonQuizViewSet,
    PurchaseCourse,
    CheckDiscountCodeValidaity,
    MyLearningDashboard,
    UserCourseStreakView,
    ReportCardView,
    PortfolioProjectsViewSet,
    StudentProgressPorfolioSection,
    UserDashboardStat,
    FlashcardViewSet,
    LibraryViewSet,
)

# Create a router and register the CoursePathWayViewSet
router = DefaultRouter()
router.register(r"course-pathways", CoursePathWayViewSet, basename="course-pathway")
router.register(r"courses", CourseViewSet, basename="course")
router.register(r"modules", ModuleViewSet, basename="module")
router.register(r"lessons", LessonViewSet, basename="lesson")
router.register(r"assignments", AssignmentViewSet, basename="assignment")
router.register(r"projects", CourseProjectViewSet, basename="project")
router.register(r"lesson-quizzes", LessonQuizViewSet, basename="quiz")
router.register(r"course-rating", CourseRatingViewSet, basename="course-rating")
router.register(r"lesson-rating", LessonRatingViewSet, basename="lesson-rating")
router.register(
    r"portfolio-projects", PortfolioProjectsViewSet, basename="portfolio-content"
)

router.register(r"flashcards", FlashcardViewSet, basename="flashcards")
router.register(r"library", LibraryViewSet, basename="library")


urlpatterns = [
    # Include the router's URLs
    path("", include(router.urls)),
    # path(
    #     "modules/get_modules/<str:course_id>",
    #     ModuleViewSet.as_view(
    #         {
    #             "get": "get_all",
    #         }
    #     ),
    #     name="get_modules",
    # ),
    # path(
    #     "lessons/get_lessons/<str:module_id>",
    #     LessonViewSet.as_view({"get": "get_all"}),
    #     name="get_lessons",
    # ),
    # path(
    #     "assignments/get_assignments/<str:module_id>",
    #     AssignmentViewSet.as_view({"get": "get_all"}),
    #     name="get_assignments",
    # ),
    path(
        "projects/get_projects/<str:course_id>",
        CourseProjectViewSet.as_view({"get": "get_all"}),
        name="get_projects",
    ),
    path(
        "lesson-quizzes/get-all/<str:lesson_id>",
        LessonQuizViewSet.as_view({"get": "get_all"}),
        name="get_lessons",
    ),
    path(
        "check-discount-code",
        CheckDiscountCodeValidaity.as_view(),
        name="check_discount_code",
    ),
    path("purchase-courses", PurchaseCourse.as_view(), name="purchase_course"),
    path(
        "my-learning-dashboard/pathways",
        MyLearningDashboard.as_view(
            {
                "get": "enrolled_pathways",
            }
        ),
        name="enrolled_pathways",
    ),
    path(
        "my-learning-dashboard/courses/<str:enrolled_pathway_id>",
        MyLearningDashboard.as_view(
            {
                "get": "enrolled_courses",
            }
        ),
        name="enrolled_courses",
    ),
    path(
        "my-learning-dashboard/modules/<str:enrolled_course_id>",
        MyLearningDashboard.as_view(
            {
                "get": "enrolled_modules",
            }
        ),
        name="enrolled_modules",
    ),
    path(
        "my-learning-dashboard/lesson/quiz/submit",
        MyLearningDashboard.as_view(
            {
                "post": "submit_lesson_quiz_score",
            }
        ),
        name="submit_lesson_quiz_score",
    ),
    path(
        "my-learning-dashboard/lesson/next-lesson/unlock/<str:pk>",
        MyLearningDashboard.as_view(
            {
                "get": "unlock_next_lesson",
            }
        ),
        name="unlock_next_lesson",
    ),
    path(
        "my-learning-dashboard/lesson/next-module/unlock/<str:pk>",
        MyLearningDashboard.as_view(
            {
                "get": "unlock_next_module",
            }
        ),
        name="unlock_next_module",
    ),
    path(
        "my-learning-dashboard/assignment/submit",
        MyLearningDashboard.as_view(
            {
                "post": "submit_asssignment",
            }
        ),
        name="submit_asssignment",
    ),
    path(
        "my-learning-dashboard/project/submit",
        MyLearningDashboard.as_view(
            {
                "post": "submit_project",
            }
        ),
        name="submit_project",
    ),
    path(
        "my-learning-dashboard/unlock-course",
        MyLearningDashboard.as_view(
            {
                "post": "unlock_course",
            }
        ),
        name="unlock_course",
    ),
    path(
        "my-learning-dashboard/my_badges",
        MyLearningDashboard.as_view(
            {
                "get": "my_badges",
            }
        ),
        name="my_badges",
    ),
    path(
        "my-learning-dashboard/my_video_library",
        MyLearningDashboard.as_view(
            {
                "get": "my_video_library",
            }
        ),
        name="my_video_library",
    ),
    path(
        "my-learning-dashboard/my_cerificates",
        MyLearningDashboard.as_view(
            {
                "get": "my_cerificates",
            }
        ),
        name="my_cerificates",
    ),
    path(
        "my-learning-dashboard/user-course-streak/<str:pathway_id>",
        UserCourseStreakView.as_view(),
        name="user_course_streak",
    ),
    path(
        "my-learning-dashboard/report-card/<str:course_id>/<str:user_id>",
        ReportCardView.as_view(),
        name="report_card",
    ),
    path(
        "my-learning-dashboard/dashbaord-stat",
        UserDashboardStat.as_view(),
        name="dashboard-stat",
    ),
    path(
        "my-learning-dashboard/detailed_module/<str:module_id>",
        MyLearningDashboard.as_view(
            {
                "get": "detailed_module",
            }
        ),
        name="detailed_module",
    ),
    path(
        "my-learning-dashboard/assignment--submission-response/<str:pk>",
        MyLearningDashboard.as_view(
            {
                "get": "get_assignment_response",
            }
        ),
        name="get_assignment_response",
    ),
    path(
        "my-learning-dashboard/project-submission-response/<str:pk>",
        MyLearningDashboard.as_view(
            {
                "get": "get_project_response",
            }
        ),
        name="get_project_response",
    ),
    path(
        "portfolio/student-progress",
        StudentProgressPorfolioSection.as_view(),
        name="portfolio_content",
    ),
]
