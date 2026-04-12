import requests
from django.core.mail import send_mail
from django.template.loader import render_to_string
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
import random
import datetime
from typing import Optional, Any
import string
from django.conf import settings


def sendMail(subject, template, context, recipient_list, plain_message=""):
    """
    Sends a template email with the specified parameters.

    Args:
        subject (str): The subject of the email.
        template (str): The path to the HTML template for the email body.
        context (dict): A dictionary containing context data to render in the email template.
        from_email (str): The sender's email address.
        recipient_list (list): A list of recipient email addresses.
        plain_message (str, optional): A plain text version of the email. Defaults to an empty string.
    """
    html_message = render_to_string(template, context)
    from_email = settings.EMAIL_HOST_USER
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=from_email,
        recipient_list=[recipient_list],
        html_message=html_message,
    )


def generate_random_token(length=4):
    token = "".join([str(random.randint(0, 9)) for _ in range(length)])
    return token


def generate_random_string(length: int = 3) -> Optional[str]:
    """Generate a random string of specified length consisting only of letters."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    return f'{timestamp}{"".join(random.choice(string.ascii_letters) for _ in range(length))}'


class StandardResultsSetPagination(PageNumberPagination):
    """
    Custom pagination class that extends PageNumberPagination to include additional
    metadata in the paginated response.

    Attributes:
        page_size (int): Default number of items per page.
        page_size_query_param (str): The name of the query parameter used to set the page size.
        max_page_size (int): The maximum number of items allowed per page.
    """

    page_size = 100
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        """
        Constructs a paginated response including metadata about the pagination.

        Args:
            data (list): The data to include in the paginated response.

        Returns:
            Response: A Response object with metadata and the paginated data.
        """
        current_page = self.page.number
        total_pages = self.page.paginator.num_pages
        return Response(
            {
                "count": self.page.paginator.count,
                "next": self.get_next_link(),
                "previous": self.get_previous_link(),
                "current_page": current_page,
                "total_pages": total_pages,
                "success": True,
                "message": "Success",
                "data": data,
            }
        )


def remove_special_char(s: str) -> str:
    """
    Removes leading special characters from a string if present.

    Args:
        s (str): The string from which to remove special characters.

    Returns:
        str: The string with leading special characters removed.
    """
    if s.startswith("@") or s.startswith("$"):
        return s[1:]
    return s


def send_notification(user_id, fcm_token, title, message, _type):
    """
    Sends a notification request to the given endpoint.

    Args:
        endpoint_url (str): The URL of the endpoint to send the request to.
        user_id (int): The ID of the user receiving the notification.
        fcm_token (str): The Firebase Cloud Messaging token of the user.
        title (str): The title of the notification.
        message (str): The message/content of the notification.
        _type (str): The type/category of the notification.

    Returns:
        dict: The response from the server in JSON format.
    """
    # Prepare the payload for the request
    payload = {
        "owner": user_id,
        "fcm_token": fcm_token,
        "title": title,
        "message": message,
        "type": _type,
    }

    try:
        endpoint_url = f"{settings.PUSH_NOTIFICATION_URL}/notification"
        # Make the POST request to the endpoint
        response = requests.post(endpoint_url, data=payload, timeout=10)

        # Raise an exception for HTTP errors
        response.raise_for_status()

        print(response.json())

        # Return the JSON response from the server
        return response.json()
    except requests.exceptions.RequestException as e:
        # Handle exceptions such as connection errors or invalid responses
        return {"success": False, "error": str(e)}


def rank_strings(strings):
    # Count occurrences of each string
    count_dict = {}
    for s in strings:
        count_dict[s] = count_dict.get(s, 0) + 1

    # Group strings by count
    count_groups = {}
    for s, count in count_dict.items():
        if count not in count_groups:
            count_groups[count] = []
        count_groups[count].append(s)

    # Sort counts in descending order
    sorted_counts = sorted(count_groups.keys(), reverse=True)

    # Assign ranks, sorting ties alphabetically
    rankings = {}
    current_rank = 1
    for count in sorted_counts:
        # Get strings for this count, sorted alphabetically
        strings_for_count = sorted(count_groups[count])
        for s in strings_for_count:
            rankings[s] = current_rank
            current_rank += 1

    # Create result list with string and its rank
    result = [(s, rankings[s]) for s in count_dict]
    # Sort by rank, then by string for same ranks
    result.sort(key=lambda x: (x[1], x[0]))

    return result
