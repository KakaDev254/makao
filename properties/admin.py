from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .models import Agent, Category, Property, PropertyImage, SavedProperty


# ------------------------------------------------------------------
# Agents
# ------------------------------------------------------------------
@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ("thumbnail", "name", "phone", "email", "property_count", "is_verified")
    list_filter = ("is_verified", "created_at")
    search_fields = ("name", "phone", "email", "slug")
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ("preview_photo", "created_at", "updated_at")
    list_per_page = 25

    fieldsets = (
        ("Identity", {
            "fields": ("name", "slug", "is_verified"),
        }),
        ("Contact", {
            "fields": ("phone", "email"),
            "description": "Include country code in phone. WhatsApp links use the 2547... format.",
        }),
        ("Profile", {
            "fields": ("bio", "photo", "preview_photo"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="")
    def thumbnail(self, obj):
        url = obj.photo_url
        if url:
            return format_html('<img src="{}" alt="" class="mk-thumb">', url)
        return mark_safe('<div class="mk-thumb-fallback">No img</div>')

    @admin.display(description="Preview")
    def preview_photo(self, obj):
        url = obj.photo_url
        if url:
            return format_html(
                '<img src="{}" alt="" style="max-width:200px;border:1px solid #e2e6ee">',
                url,
            )
        return mark_safe(
            '<div style="padding:16px;background:#f1f4f9;border:1px solid #e2e6ee;'
            'color:#a18f83;font-size:12px;text-transform:uppercase;letter-spacing:.05em">'
            'No photo yet</div>'
        )

    @admin.display(description="Listings")
    def property_count(self, obj):
        return obj.properties.filter(is_active=True, is_pending=False).count()


# ------------------------------------------------------------------
# Categories
# ------------------------------------------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "tagline", "sort_order", "property_count")
    list_editable = ("sort_order",)
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "slug")

    @admin.display(description="Listings")
    def property_count(self, obj):
        return obj.properties.filter(is_active=True, is_pending=False).count()


# ------------------------------------------------------------------
# Custom filters
# ------------------------------------------------------------------
class PriceBandFilter(admin.SimpleListFilter):
    title = "price band (KES)"
    parameter_name = "price_band"

    def lookups(self, request, model_admin):
        return [
            ("lt_1m",   "Under 1M"),
            ("1m_10m",  "1M – 10M"),
            ("10m_50m", "10M – 50M"),
            ("gt_50m",  "Over 50M"),
        ]

    def queryset(self, request, queryset):
        v = self.value()
        if v == "lt_1m":
            return queryset.filter(price__lt=1_000_000)
        if v == "1m_10m":
            return queryset.filter(price__gte=1_000_000, price__lt=10_000_000)
        if v == "10m_50m":
            return queryset.filter(price__gte=10_000_000, price__lt=50_000_000)
        if v == "gt_50m":
            return queryset.filter(price__gte=50_000_000)
        return queryset


# ------------------------------------------------------------------
# Property Gallery Inline
# ------------------------------------------------------------------
class PropertyImageInline(admin.TabularInline):
    model = PropertyImage
    fk_name = "property_ref"  # Points to the renamed ForeignKey field
    extra = 3    # Shows 3 empty upload fields by default
    max_num = 4  # Enforces the max of 4 images per property
    can_delete = True


# ------------------------------------------------------------------
# Properties
# ------------------------------------------------------------------
@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):
    list_display = (
        "thumbnail", "title", "category_pill", "location_col",
        "price_col", "specs_col", "flags_col", "pending_pill",
    )
    list_display_links = ("title",)
    list_filter = (
        "category", "county", PriceBandFilter, "property_type", "agent",
        "is_pending", "is_featured", "is_verified", "is_active", "created_at",
    )
    search_fields = (
        "title", "neighborhood", "county", "slug",
        "agent__name", "agent__phone",
        "agent_name", "agent_phone",
    )
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_at", "updated_at", "preview_image")
    list_per_page = 25
    date_hierarchy = "created_at"
    save_on_top = True
    actions = ("approve_listings", "reject_listings")
    inlines = [PropertyImageInline]

    fieldsets = (
        ("Listing", {
            "fields": ("category", "title", "slug", "description")
        }),
        ("Location", {
            "fields": ("county", "neighborhood")
        }),
        ("Classification & Pricing", {
            "fields": ("property_type", "price", "price_period")
        }),
        ("Specs", {
            "fields": ("bedrooms", "bathrooms", "guests", "area_sqft", "plot_size")
        }),
        ("Media", {
            "fields": ("cover_image", "preview_image"),
            "description": "Upload a cover image. Stored on Cloudinary under makao/properties.",
        }),
        ("Visibility", {
            "fields": ("is_pending", "is_verified", "is_featured", "is_active"),
            "description": "Approved listings need is_pending=False and is_active=True.",
        }),
        ("Contact", {
            "fields": ("agent", "agent_name", "agent_phone"),
            "description": (
                "Preferred: pick an Agent. Fallback: enter name and phone "
                "(for quick edits or pre-migration rows)."
            ),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )

    # ---------- list columns ----------

    @admin.display(description="")
    def thumbnail(self, obj):
        url = obj.cover_url
        if url:
            return format_html('<img src="{}" alt="" class="mk-thumb">', url)
        return mark_safe('<div class="mk-thumb-fallback">No img</div>')

    @admin.display(description="Category", ordering="category__sort_order")
    def category_pill(self, obj):
        slug = obj.category.slug if obj.category_id else "default"
        return format_html(
            '<span class="mk-pill mk-pill--{}">{}</span>', slug, obj.category.name
        )

    @admin.display(description="Location", ordering="county")
    def location_col(self, obj):
        return format_html(
            '<strong>{}</strong><br><span style="color:#6b7280;font-size:12px">{}</span>',
            obj.neighborhood, obj.county,
        )

    @admin.display(description="Price", ordering="price")
    def price_col(self, obj):
        return format_html("<strong>{}</strong>", obj.price_display)

    @admin.display(description="Specs")
    def specs_col(self, obj):
        bits = []
        if obj.bedrooms:  bits.append(f"{obj.bedrooms}bd")
        if obj.bathrooms: bits.append(f"{obj.bathrooms}ba")
        if obj.guests:    bits.append(f"{obj.guests}g")
        if obj.plot_size: bits.append(obj.plot_size)
        if obj.area_sqft: bits.append(f"{obj.area_sqft:,} sqft")
        return " · ".join(bits) if bits else "—"

    @admin.display(description="Flags")
    def flags_col(self, obj):
        pills = []
        pills.append(
            '<span class="mk-pill mk-pill--{}">{}</span>'.format(
                "on" if obj.is_active else "off",
                "Active" if obj.is_active else "Hidden",
            )
        )
        if obj.is_featured:
            pills.append('<span class="mk-pill mk-pill--feat">Featured</span>')
        if obj.is_verified:
            pills.append('<span class="mk-pill mk-pill--on">Verified</span>')
        return mark_safe(" ".join(pills))

    @admin.display(description="Review", ordering="is_pending")
    def pending_pill(self, obj):
        if obj.is_pending:
            return mark_safe('<span class="mk-pill mk-pill--feat">Pending</span>')
        return mark_safe('<span class="mk-pill mk-pill--on">Reviewed</span>')

    # ---------- detail form ----------

    @admin.display(description="Preview")
    def preview_image(self, obj):
        url = obj.cover_url
        if url:
            return format_html(
                '<img src="{}" alt="" style="max-width:320px;border:1px solid #e2e6ee">',
                url,
            )
        return mark_safe(
            '<div style="padding:24px;background:#f1f4f9;border:1px solid #e2e6ee;'
            'color:#a18f83;font-size:12px;text-transform:uppercase;letter-spacing:.05em">'
            'No cover image yet</div>'
        )

    # ---------- bulk actions ----------

    @admin.action(description="Approve selected listings (make them live)")
    def approve_listings(self, request, queryset):
        updated = queryset.update(is_pending=False, is_active=True)
        self.message_user(
            request,
            f"{updated} listing(s) approved and published.",
        )

    @admin.action(description="Reject selected listings (keep hidden)")
    def reject_listings(self, request, queryset):
        updated = queryset.update(is_pending=False, is_active=False)
        self.message_user(
            request,
            f"{updated} listing(s) rejected.",
        )


# ------------------------------------------------------------------
# Saved properties
# ------------------------------------------------------------------
@admin.register(SavedProperty)
class SavedPropertyAdmin(admin.ModelAdmin):
    list_display = ("who", "property_link", "created_at")
    list_filter = ("created_at", "user")
    search_fields = ("session_key", "user__email", "user__username", "property__title")
    raw_id_fields = ("user", "property")

    @admin.display(description="Who")
    def who(self, obj):
        if obj.user_id:
            return obj.user.email or obj.user.username
        if obj.session_key:
            return f"anon:{obj.session_key[:10]}…"
        return "—"

    @admin.display(description="Property")
    def property_link(self, obj):
        url = f"/admin/properties/property/{obj.property_id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.property.title)