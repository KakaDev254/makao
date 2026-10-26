from django.http import HttpResponse
from django.db.models import Q
from django.shortcuts import render

from properties.models import Category, Property


def home(request):
    categories = Category.objects.all()
    properties_list = (
        Property.objects.active()
        .select_related("category")
        .order_by("-is_featured", "-created_at")[:12]
    )
    context = {
        "categories": categories,
        "properties_list": properties_list,
        "hero_image": (
            "https://images.unsplash.com/photo-1613490493576-7fde63acd811"
            "?auto=format&fit=crop&w=2000&q=80"
        ),
    }
    return render(request, "core/home.html", context)


def search(request):
    """Public search results page. Reuses the same filters as the listings grid."""
    qs = Property.objects.active().select_related("category")

    q = request.GET.get("q", "").strip()
    category = request.GET.get("category", "").strip()
    ptype = request.GET.get("type", "").strip()
    max_price = request.GET.get("max", "").strip()

    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(neighborhood__icontains=q)
            | Q(county__icontains=q)
        )

    if category and category != "all":
        qs = qs.filter(category__slug=category)

    if ptype:
        qs = qs.filter(property_type=ptype)

    if max_price:
        try:
            qs = qs.filter(price__lte=int(max_price))
        except (TypeError, ValueError):
            pass

    qs = qs.order_by("-is_featured", "-created_at")

    context = {
        "properties": qs,
        "result_count": qs.count(),
        "categories": Category.objects.all(),
        "query": q,
        "active_category": category or "all",
        "active_type": ptype,
        "active_max": max_price,
    }
    return render(request, "core/search.html", context)

def saved(request):
    return render(request, "core/saved.html")



def robots_txt(request):
    return render(
        request,
        "robots.txt",
        content_type="text/plain",
    )


def sitemap_xml(request):
    properties = Property.objects.active().only("slug", "updated_at")
    return render(
        request,
        "sitemap.xml",
        {"properties": properties},
        content_type="application/xml",
    )
    
def error_404(request, exception=None):
    return render(request, "404.html", status=404)


def error_500(request):
    return render(request, "500.html", status=500)