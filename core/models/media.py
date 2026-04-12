import os
import uuid
from django.db import models
from support.models.mixims import TouchDatesMixim


def get_file_category(file_extension):
    """
    Determine the file category based on its extension
    """
    extension = file_extension.lower()

    # Map of file extensions to their categories
    EXTENSION_CATEGORIES = {
        # Images
        ".jpg": "photo",
        ".jpeg": "photo",
        ".png": "photo",
        ".gif": "photo",
        ".webp": "photo",
        # Videos
        ".mp4": "video",
        ".mov": "video",
        ".avi": "video",
        ".webm": "video",
        # Documents
        ".pdf": "document",
        ".doc": "document",
        ".docx": "document",
        ".txt": "document",
        # Spreadsheets
        ".xls": "spreadsheet",
        ".xlsx": "spreadsheet",
        ".csv": "spreadsheet",
        # Presentations
        ".ppt": "presentation",
        ".pptx": "presentation",
        # Archives
        ".zip": "archive",
        ".rar": "archive",
        ".7z": "archive",
    }

    return EXTENSION_CATEGORIES.get(extension, "other")


def media_file_path(instance, filename):
    # Get file extension
    _, file_extension = os.path.splitext(filename)

    # Generate a new filename with a random UUID
    new_filename = f"{uuid.uuid4()}{file_extension}"

    # Get the file category
    category = get_file_category(file_extension)

    # Define base paths for different environments
    if instance.is_fake_data:
        base_path = "seed_media"
    else:
        base_path = ""

    # Return appropriate path based on file category
    return os.path.join(base_path, category, new_filename)


class Media(TouchDatesMixim):
    MEDIA_TYPES = (
        ("photo", "Photo"),
        ("video", "Video"),
        ("document", "Document"),
        ("spreadsheet", "Spreadsheet"),
        ("presentation", "Presentation"),
        ("archive", "Archive"),
        ("other", "Other"),
    )

    media_type = models.CharField(max_length=15, choices=MEDIA_TYPES)
    media = models.FileField(upload_to=media_file_path, null=True, blank=True)
    metadata = models.JSONField(default=dict, null=True, blank=True)
    cover_art = models.ImageField(upload_to="cover_arts", null=True, blank=True)
    downloaded_media = models.BooleanField(default=False, null=True, blank=True)
    downloaded_media_url = models.URLField(null=True, blank=True, unique=True)

    class Meta:
        verbose_name_plural = "Media"

    def __str__(self):
        return f"{self.media_type}"
