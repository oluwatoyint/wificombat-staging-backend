from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from core.models.courses import Course, Module, Badge


@receiver(post_save, sender=Course)
def create_or_update_course_badge(sender, instance, created, **kwargs):
    """
    Signal to create or update a badge when a Course is created or updated.
    """
    content_type = ContentType.objects.get_for_model(instance)
    badge, badge_created = Badge.objects.get_or_create(
        content_type=content_type,
        object_id=instance.id,
        defaults={
            "name": f"Course Badge - {instance.title}",
            "description": f"Awarded for completing the course: {instance.title}",
            "icon": instance.badge_icon,  # Pass the badge_icon from the Course instance
        },
    )

    # If the badge already exists and the instance is being updated, update the icon
    if not badge_created:
        badge.icon = instance.badge_icon
        badge.save()


@receiver(post_save, sender=Module)
def create_or_update_module_badge(sender, instance, created, **kwargs):
    """
    Signal to create or update a badge when a Module is created or updated.
    """
    content_type = ContentType.objects.get_for_model(instance)
    badge, badge_created = Badge.objects.get_or_create(
        content_type=content_type,
        object_id=instance.id,
        defaults={
            "name": f"Module Badge - {instance.title}",
            "description": f"Awarded for completing the module: {instance.title}",
            "icon": instance.badge_icon,  # Pass the badge_icon from the Module instance
        },
    )

    # If the badge already exists and the instance is being updated, update the icon
    if not badge_created:
        badge.icon = instance.badge_icon
        badge.save()
