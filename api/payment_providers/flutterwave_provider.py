import time
from .base_payment_providers import BasePaymentProvider
from django.conf import settings
import requests


class FlutterwaveProvider(BasePaymentProvider):
    """fluterwave payment provider"""

    def __init__(self):
        self.base_url = "https://api.flutterwave.com/v3"
        self.secret_key = settings.FLUTTERWAVE_SECRET_KEY
        self.public_key = settings.FLUTTERWAVE_PUBLIC_KEY
        self.webhook_url = settings.FLUTTERWAVE_WEBHOOK_URL
        self.headers = {
            "Authorization": f"Bearer {self.secret_key}",
            "Content-Type": "application/json",
        }

    def initialize_payment(self, **kwargs):
        """Initialize payment process"""
        try:
            amount = kwargs.get("amount", 0)
            user = kwargs.get("user", None)
            success_url = kwargs.get("success_url")
            
            payload = {
                "tx_ref": self.generate_transaction_reference(user),
                "amount": amount,
                "currency": "NGN",
                "redirect_url": success_url,
                "customer": {
                    "email": user.email,
                    "name": kwargs.get("customer_name", ""),
                },
                "meta": kwargs.get("metadata", {}),
            }

            response = requests.post(
                f"{self.base_url}/payments",
                headers=self.headers,
                json=payload,
                timeout=30,
            )

            response.raise_for_status()  # Raise an HTTPError if the response was not successful

            data = response.json()
            return data

        except requests.exceptions.HTTPError as http_err:
            # Catch HTTP errors
            print(f"HTTP error occurred: {http_err}")
            raise

        except requests.exceptions.ConnectionError as conn_err:
            # Catch connection errors
            print(f"Connection error occurred: {conn_err}")
            raise

        except requests.exceptions.Timeout as timeout_err:
            # Catch timeout errors
            print(f"Timeout error occurred: {timeout_err}")
            raise

        except requests.exceptions.RequestException as req_err:
            # Catch all other request exceptions
            print(f"Request error occurred: {req_err}")
            raise

        except KeyError as key_err:
            # Catch key errors when accessing dictionary keys
            print(f"Key error: {key_err}")
            raise

        except Exception as e:
            # Catch any other general exception
            print(f"An unexpected error occurred: {str(e)}")
            raise

    def generate_transaction_reference(self, user):
        """
        Generate a unique transaction reference including the user's email.

        Args:
            user: the user
        Returns:
            str: A unique transaction reference.
        """
        timestamp = int(time.time())  # Get the current time as a Unix timestamp
        unique_id = str(user.id)  # Generate a random unique ID
        sanitized_email = user.email.split("@")[
            0
        ]  # Use the part before "@" in the email

        # Combine parts to form the transaction reference
        tx_ref = f"{sanitized_email.upper()}_{timestamp}_{unique_id}"
        return tx_ref
