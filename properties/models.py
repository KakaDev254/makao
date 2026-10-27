from django.db import models
from django.utils.text import slugify

from cloudinary.models import CloudinaryField


class Category(models.Model):
    """Top-level buckets: Airbnbs, Rentals, Land, For Sale."""

    class Slug(models.TextChoices):
        AIRBNB = "airbnb", "Airbnbs"
        RENTAL = "rental", "Rentals"
        LAND   = "land",   "Land"
        SALE   = "sale",   "For sale"

    slug = models.SlugField(max_length=32, unique=True)
    name = models.CharField(max_length=64)
    tagline = models.CharField(max_length=120, blank=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

    @property
    def landing_url_name(self):
        return {
            "airbnb": "properties:airbnbs",
            "rental": "properties:rentals",
            "land":   "properties:land",
            "sale":   "properties:for_sale",
        }.get(self.slug, "properties:listings")


class PropertyQuerySet(models.QuerySet):
    def active(self):
        return self.filter(is_active=True, is_pending=False)

    def featured(self):
        return self.filter(is_featured=True, is_active=True)


class Agent(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    phone = models.CharField(max_length=32, help_text="Include country code. E.g. 254712345678")
    email = models.EmailField(blank=True)
    bio = models.TextField(blank=True, help_text="Optional short biography.")
    photo = CloudinaryField("photo", folder="makao/agents", blank=True, null=True, overwrite=False, resource_type="image")
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Agents"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name)[:120]
            slug = base
            counter = 1
            while Agent.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base[:115]}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def photo_url(self):
        if not self.photo:
            return ""
        url = getattr(self.photo, "url", "") or ""
        if url.startswith("http://"):
            url = "https://" + url[len("http://"):]
        return url

    @property
    def initial(self):
        return (self.name or "?").strip()[:1].upper()


class Property(models.Model):
    class PropertyType(models.TextChoices):
        APARTMENT = "apartment", "Apartment"
        VILLA     = "villa",     "Villa"
        HOUSE     = "house",     "House"
        STUDIO    = "studio",    "Studio"
        LAND      = "land",      "Land"
        ANY       = "any",       "Any"

    class PricePeriod(models.TextChoices):
        NIGHT = "night", "Night"
        MONTH = "month", "Month"
        TOTAL = "total", "Total"

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="properties")
    title = models.CharField(max_length=180)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField(blank=True)
    county = models.CharField(max_length=64, db_index=True)
    neighborhood = models.CharField(max_length=120, db_index=True)
    property_type = models.CharField(max_length=16, choices=PropertyType.choices, default=PropertyType.APARTMENT)
    price = models.PositiveBigIntegerField(help_text="Price in KES")
    price_period = models.CharField(max_length=8, choices=PricePeriod.choices, default=PricePeriod.TOTAL)
    
    bedrooms  = models.PositiveSmallIntegerField(null=True, blank=True)
    bathrooms = models.PositiveSmallIntegerField(null=True, blank=True)
    guests    = models.PositiveSmallIntegerField(null=True, blank=True)
    area_sqft = models.PositiveIntegerField(null=True, blank=True)
    plot_size = models.CharField(max_length=64, blank=True)

    cover_image = CloudinaryField("cover_image", folder="makao/properties", blank=True, null=True, overwrite=False, resource_type="image")

    is_verified = models.BooleanField(default=False)
    is_featured = models.BooleanField(default=False)
    is_active   = models.BooleanField(default=True)
    is_pending  = models.BooleanField(default=False, help_text="Awaiting admin review")

    agent = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name="properties", null=True, blank=True)
    agent_name  = models.CharField(max_length=120, blank=True)
    agent_phone = models.CharField(max_length=32, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PropertyQuerySet.as_manager()

    class Meta:
        ordering = ["-is_featured", "-created_at"]
        indexes = [
            models.Index(fields=["category", "county"]),
            models.Index(fields=["is_active", "is_featured"]),
        ]
        verbose_name_plural = "Properties"

    def __str__(self):
        return f"{self.title} — {self.neighborhood}, {self.county}"

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(f"{self.title}-{self.neighborhood}-{self.county}")
            slug = base[:200]
            counter = 1
            while Property.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base[:195]}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def price_display(self):
        formatted = f"KSh {self.price:,}"
        if self.price_period in (self.PricePeriod.NIGHT, self.PricePeriod.MONTH):
            return f"{formatted} / {self.price_period}"
        return formatted

    @property
    def cover_url(self):
        if not self.cover_image:
            return ""
        url = getattr(self.cover_image, "url", "") or ""
        if url.startswith("http://"):
            url = "https://" + url[len("http://"):]
        return url


class PropertyImage(models.Model):
    property_ref = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    image = CloudinaryField("image", folder="makao/properties/gallery", blank=True, null=True, overwrite=False, resource_type="image")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Image for {self.property_ref.title}"

    @property
    def image_url(self):
        if not self.image:
            return ""
        url = getattr(self.image, "url", "") or ""
        if url.startswith("http://"):
            url = "https://" + url[len("http://"):]
        return url


class SavedProperty(models.Model):
    user = models.ForeignKey("auth.User", on_delete=models.CASCADE, null=True, blank=True, related_name="saved_properties")
    session_key = models.CharField(max_length=64, db_index=True, blank=True)
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="saves")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "property"], condition=models.Q(user__isnull=False), name="unique_user_property_save"),
            models.UniqueConstraint(fields=["session_key", "property"], condition=models.Q(user__isnull=True), name="unique_session_property_save"),
        ]

    def __str__(self):
        who = self.user.email if self.user_id else f"session:{self.session_key[:8]}"
        return f"save:{who} → {self.property_id}"