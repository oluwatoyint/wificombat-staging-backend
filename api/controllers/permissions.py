from rest_framework.permissions import BasePermission


class IsSchoolAdmin(BasePermission):
    """
    Custom permission to check if the user is a school admin.
    """

    message = "You do not have permission to perform this action."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            self.message = "Authentication is required to perform this action."
            return False

        if request.user.role != request.user.Roles.SCHOOL_ADMIN:
            return False

        return True
