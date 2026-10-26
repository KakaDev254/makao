from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver

from cloudinary.models import CloudinaryField


class Profile(models.Model):
    """Extra user data that doesn't belong on Django's User model."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )

    display_name = models.CharField(
        max_length=80,
        blank=True,
        help_text="Shown on Makao instead of your full name.",
    )
    phone = models.CharField(
        max_length=32,
        blank=True,
        help_text="Include country code. E.g. 254712345678",
    )
    county = models.CharField(
        max_length=64,
        blank=True,
        help_text="The county you're based in or most interested in.",
    )
    bio = models.TextField(
        max_length=280,
        blank=True,
        help_text="A short line about yourself. Max 280 characters.",
    )
    avatar = CloudinaryField(
        "avatar",
        folder="makao/avatars",
        blank=True,
        null=True,
        overwrite=True,
        resource_type="image",
    )

    notify_email_on_inquiry = models.BooleanField(
        default=True,
        help_text="Email me when someone inquires about my listings.",
    )
    notify_price_drops = models.BooleanField(
        default=False,
        help_text="Email me about price drops on saved properties.",
    )
    notify_new_listings = models.BooleanField(
        default=False,
        help_text="Email me about new listings matching my searches.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Profiles"

    def __str__(self):
        return f"Profile: {self.user.email or self.user.username}"

    @property
    def avatar_url(self):
        if not self.avatar:
            return ""
        url = getattr(self.avatar, "url", "") or ""
        if url.startswith("http://"):
            url = "https://" + url[len("http://"):]
        return url

    @property
    def name(self):
        if self.display_name:
            return self.display_name
        full = self.user.get_full_name().strip()
        if full:
            return full
        return self.user.email.split("@")[0] if self.user.email else self.user.username

    @property
    def initial(self):
        return (self.name or "?").strip()[:1].upper()


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def ensure_profile(sender, instance, created, **kwargs):
    """Every new user gets a Profile row automatically."""
    if created:
        Profile.objects.create(user=instance)