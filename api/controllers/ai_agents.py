import logging, json, asyncio
from rest_framework import status, permissions, viewsets
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.translation import gettext as _
from support import helpers, http
from core.managers import utils
from api.agents.quiz_grading_agent import QuizGraderAgent
from api.agents.assignment_grader import ProjectAndAssignmentGraderAgent

logger = logging.getLogger(__name__)
User = get_user_model()


class AIAgent(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["post"])
    def grade_quiz(self, request):  # Remove async
        payload = request.data.get("payload")
        if not payload:
            return http.failed_response(None, _("Payload is required."))

        agent = QuizGraderAgent(payload)
        # Use asyncio to run the async function
        result = asyncio.run(agent.run())
        return http.success_response(data=result)

    @action(detail=False, methods=["post"])
    def grade_assignment_or_projects(self, request):  # Remove async
        payload = request.data.get("payload")
        if not payload:
            return http.failed_response(None, _("Payload is required."))

        agent = ProjectAndAssignmentGraderAgent(payload)
        # Use asyncio to run the async function
        result = asyncio.run(agent.run())
        return http.success_response(data=result)
