from urllib.parse import quote

from django.contrib import messages
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.views.decorators.http import require_GET, require_POST

from .forms import PropertySubmissionForm
from .models import Agent, Category, Property, SavedProperty


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _filter_queryset(request):
    """Shared filter logic for the listings view and the JSON API."""
    qs = Property.objects.active().select_related("category")

    category = request.GET.get("category")
    if category and category != "all":
        qs = qs.filter(category__slug=category)

    q = request.GET.get("q")
    if q:
        qs = qs.filter(
            models.Q(title__icontains=q)
            | models.Q(neighborhood__icontains=q)
            | models.Q(county__icontains=q)
        )

    ptype = request.GET.get("type")
    if ptype:
        qs = qs.filter(property_type=ptype)

    max_price = request.GET.get("max")
    if max_price:
        try:
            qs = qs.filter(price__lte=int(max_price))
        except (TypeError, ValueError):
            pass

    return qs


def _agent_name_phone(p):
    """Return (name, phone) preferring the linked Agent over legacy fields."""
    if getattr(p, "agent_id", None) and p.agent:
        return (p.agent.name, p.agent.phone)
    return (p.agent_name or "", p.agent_phone or "")


def _whatsapp_url(p):
    """Build a wa.me link with a prefilled message."""
    name, phone_raw = _agent_name_phone(p)
    phone = "".join(ch for ch in (phone_raw or "") if ch.isdigit())
    msg = f"Hi {name}, I'm interested in \"{p.title}\" on Makao."
    return f"https://wa.me/{phone}?text={quote(msg)}"


def _saved_slugs_for(request):
    """Return the list of slugs saved for this user or session."""
    if request.user.is_authenticated:
        qs = SavedProperty.objects.filter(user=request.user).select_related("property")
    else:
        if not request.session.session_key:
            request.session.create()
        qs = SavedProperty.objects.filter(
            session_key=request.session.session_key
        ).select_related("property")
    return [s.property.slug for s in qs]


# ------------------------------------------------------------------
# Listings & detail endpoints
# ------------------------------------------------------------------

@require_GET
def listings(request):
    """Return the listings grid as an HTML partial (used by JS to swap content)."""
    qs = _filter_queryset(request)
    categories = Category.objects.all()
    return render(
        request,
        "partials/_listings_results.html",
        {
            "properties": qs,
            "categories": categories,
            "active_category": request.GET.get("category", "all"),
            "result_count": qs.count(),
        },
    )


@require_GET
def property_detail_json(request, slug):
    """Return one property as JSON for the modal."""
    p = get_object_or_404(
        Property.objects.select_related("category", "agent"),
        slug=slug,
        is_active=True,
    )
    name, phone = _agent_name_phone(p)

    return JsonResponse(
        {
            "slug": p.slug,
            "title": p.title,
            "description": p.description or "No description provided.",
            "category": p.category.name,
            "category_slug": p.category.slug,
            "county": p.county,
            "neighborhood": p.neighborhood,
            "property_type": p.get_property_type_display(),
            "price_display": p.price_display,
            "price_raw": p.price,
            "bedrooms": p.bedrooms,
            "bathrooms": p.bathrooms,
            "guests": p.guests,
            "area_sqft": p.area_sqft,
            "plot_size": p.plot_size,
            "cover_image": p.cover_url,
            "is_verified": p.is_verified,
            "is_featured": p.is_featured,
            "agent_name": name,
            "agent_phone": phone,
            "agent_slug": p.agent.slug if p.agent_id else "",
            "whatsapp_url": _whatsapp_url(p),
            "call_url": f"tel:+{phone}",
        }
    )


@require_GET
def listings_by_slugs(request):
    """Return a listings grid for a comma-separated list of slugs.
    Used by the /saved/ page."""
    raw = request.GET.get("slugs", "").strip()
    slugs = [s.strip() for s in raw.split(",") if s.strip()]

    if not slugs:
        return render(
            request,
            "partials/_listings_results.html",
            {"properties": [], "categories": Category.objects.all()},
        )

    qs = (
        Property.objects.active()
        .filter(slug__in=slugs)
        .select_related("category")
    )
    order = {slug: i for i, slug in enumerate(slugs)}
    properties = sorted(qs, key=lambda p: order.get(p.slug, 999))

    return render(
        request,
        "partials/_listings_results.html",
        {"properties": properties, "categories": Category.objects.all()},
    )


def property_detail(request, slug):
    """Full detail page for one property."""
    p = get_object_or_404(
        Property.objects.select_related("category", "agent"),
        slug=slug,
        is_active=True,
    )

    related = (
        Property.objects.active()
        .filter(category=p.category)
        .exclude(pk=p.pk)
        .order_by("-is_featured", "-created_at")[:4]
    )

    return render(
        request,
        "properties/detail.html",
        {
            "property": p,
            "related": related,
        },
    )


# ------------------------------------------------------------------
# Category landing
# ------------------------------------------------------------------

CATEGORY_META = {
    "airbnb": {
        "eyebrow": "Short stays",
        "title": "Airbnbs in Kenya",
        "sub": "Weekend escapes, coastal villas, city lofts, and safari lodges.",
    },
    "rental": {
        "eyebrow": "Long-term",
        "title": "Rentals in Kenya",
        "sub": "Family homes, city apartments, and commercial spaces across the country.",
    },
    "land": {
        "eyebrow": "Invest",
        "title": "Land in Kenya",
        "sub": "Plots, parcels, and acres — ready to build, hold, or develop.",
    },
    "sale": {
        "eyebrow": "Own it",
        "title": "Properties for sale",
        "sub": "Houses, apartments, and estates with verified titles.",
    },
}


def category_landing(request, slug):
    """Public category landing page."""
    category = get_object_or_404(Category, slug=slug)
    meta = CATEGORY_META.get(slug, {
        "eyebrow": "Browse",
        "title": category.name,
        "sub": category.tagline or "",
    })

    qs = (
        Property.objects.active()
        .filter(category=category)
        .select_related("category")
        .order_by("-is_featured", "-created_at")
    )

    context = {
        "category": category,
        "meta": meta,
        "properties": qs,
        "result_count": qs.count(),
        "categories": Category.objects.all(),
    }
    return render(request, "properties/category.html", context)


# ------------------------------------------------------------------
# Submission flow
# ------------------------------------------------------------------

def submit_property(request):
    """Public form for hosts, landlords, and sellers to submit a listing."""
    if request.method == "POST":
        form = PropertySubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            prop = form.save(commit=False)
            prop.is_pending = True
            prop.is_active = False
            prop.is_featured = False
            prop.is_verified = False
            prop.save()
            return redirect("properties:submit_success")
    else:
        form = PropertySubmissionForm()

    return render(request, "properties/submit.html", {"form": form})


def submit_success(request):
    """Thank-you page after a successful submission."""
    return render(request, "properties/submit_success.html")


# ------------------------------------------------------------------
# Agent profile
# ------------------------------------------------------------------

def agent_detail(request, slug):
    """Public profile page for an agent."""
    agent = get_object_or_404(Agent, slug=slug)

    listings = (
        Property.objects.active()
        .filter(agent=agent)
        .select_related("category")
        .order_by("-is_featured", "-created_at")
    )

    context = {
        "agent": agent,
        "listings": listings,
        "listing_count": listings.count(),
    }
    return render(request, "properties/agent_detail.html", context)


# ------------------------------------------------------------------
# Saved properties — JSON API
# ------------------------------------------------------------------

@require_GET
def saved_slugs(request):
    """Return slugs the current user/session has saved."""
    return JsonResponse({"slugs": _saved_slugs_for(request)})


@require_POST
def save_toggle(request):
    """Toggle a save for the current user or session.
    POST body: slug=<slug>"""
    slug = request.POST.get("slug", "").strip()
    if not slug:
        return JsonResponse({"ok": False, "error": "missing slug"}, status=400)

    try:
        prop = Property.objects.get(slug=slug, is_active=True, is_pending=False)
    except Property.DoesNotExist:
        return JsonResponse({"ok": False, "error": "not found"}, status=404)

    if request.user.is_authenticated:
        qs = SavedProperty.objects.filter(user=request.user, property=prop)
        existing = qs.first()
        if existing:
            existing.delete()
            saved = False
        else:
            SavedProperty.objects.create(user=request.user, property=prop)
            saved = True
    else:
        if not request.session.session_key:
            request.session.create()
        sk = request.session.session_key
        qs = SavedProperty.objects.filter(session_key=sk, property=prop)
        existing = qs.first()
        if existing:
            existing.delete()
            saved = False
        else:
            SavedProperty.objects.create(session_key=sk, property=prop)
            saved = True

    return JsonResponse({"ok": True, "saved": saved, "slug": slug})


@require_POST
def saved_merge(request):
    """Merge localStorage slugs into the user's saved list after login.
    POST body: slugs=slug1,slug2,slug3"""
    if not request.user.is_authenticated:
        return JsonResponse({"ok": False, "error": "auth required"}, status=403)

    raw = request.POST.get("slugs", "").strip()
    slugs = [s.strip() for s in raw.split(",") if s.strip()]
    if not slugs:
        return JsonResponse({"ok": True, "added": 0})

    props = Property.objects.filter(slug__in=slugs, is_active=True, is_pending=False)
    added = 0
    for p in props:
        _, created = SavedProperty.objects.get_or_create(
            user=request.user,
            property=p,
        )
        if created:
            added += 1

    return JsonResponse({"ok": True, "added": added})