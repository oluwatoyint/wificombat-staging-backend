from django.db.models.signals import post_save
from django.dispatch import receiver
from core.models.users import User, Wallet


@receiver(post_save, sender=User)
def create_user_wallet(sender, instance, created, **kwargs):
    """
    Signal to automatically create a wallet when a new user is created
    """
    if created:
        if instance.role in ["user", "student"]:
            """ensure wallet is only created for students or user"""
            Wallet.objects.create(user=instance)
