from .flutterwave_provider import FlutterwaveProvider


class PaymentProviderFactory:
    """Factory class to create payment providers"""

    @staticmethod
    def create_provider(provider_type: str):
        """
        Create a payment provider based on the provided type.

        Args:
            provider_type (str): The type of payment provider to create.
            Defaults to "flutterwave".
        """
        # if provider_type == "flutterwave":
        #     return FlutterwaveProvider()
        
        providers = {"flutterwave": FlutterwaveProvider()}

        provider_class = providers.get(provider_type.lower())
        if not provider_class:
            raise ValueError(f"Unsupported payment provider: {provider_type}")

        return provider_class
