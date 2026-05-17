import os

from django.db.models.signals import post_delete
from django.dispatch import receiver

from .models import Music, Post, PostMedia, TimelineMedia


def _delete_file_if_exists(file_field):
    if file_field and os.path.isfile(file_field.path):
        os.remove(file_field.path)


@receiver(post_delete, sender=Post)
def post_delete_post(sender, instance, **kwargs):
    _delete_file_if_exists(instance.media)


@receiver(post_delete, sender=PostMedia)
def post_delete_post_media(sender, instance, **kwargs):
    _delete_file_if_exists(instance.file)


@receiver(post_delete, sender=Music)
def post_delete_music(sender, instance, **kwargs):
    _delete_file_if_exists(instance.file)


@receiver(post_delete, sender=TimelineMedia)
def post_delete_timeline_media(sender, instance, **kwargs):
    _delete_file_if_exists(instance.file)
