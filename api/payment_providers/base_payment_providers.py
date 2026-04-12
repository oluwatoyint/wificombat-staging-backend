from abc import ABC, abstractmethod


class BasePaymentProvider(ABC):
    """Base class all providers must have"""

    @abstractmethod
    def initialize_payment(self, **kwargs):
        """Initialize payment process"""
        pass
