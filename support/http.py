"""
Http helper functions 
"""

from rest_framework.response import Response
from rest_framework import status


def success_response(
    data=None, message="Success", status_code=status.HTTP_200_OK, *args, **kwargs
):
    """
    Send JSON API success response.

    Arguments:
        data (object): The data to send back (default: None)
        message (str): The success message (default: "Success")
        status_code (int): The HTTP status code (default: 200)

    Returns:
        Response: Django Rest Framework Response
    """
    response_data = {"success": True, "message": message}

    if data is not None:
        response_data["data"] = data

    return Response(response_data, status=status_code, *args, **kwargs)


def failed_response(
    data=None,
    message="Failed",
    status_code=status.HTTP_400_BAD_REQUEST,
    *args,
    **kwargs,
):
    """
    Send JSON API success response.

    Arguments:
        data (object): The data to send back (default: None)
        message (str): The success message (default: "Success")
        status_code (int): The HTTP status code (default: 200)

    Returns:
        Response: Django Rest Framework Response
    """
    response_data = {"success": False, "message": message}

    if data is not None:
        response_data["data"] = data

    return Response(response_data, status=status_code, *args, **kwargs)
