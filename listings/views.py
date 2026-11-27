from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect

from .forms import TicketForm
from .models import Property


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def property_list(request):
    qs = Property.objects.filter(status=Property.STATUS_ACTIVE).prefetch_related("images")

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q)
            | Q(city__icontains=q)
            | Q(neighborhood__icontains=q)
            | Q(address__icontains=q)
            | Q(description__icontains=q)
        )

    deal_type = request.GET.get("deal_type", "").strip()
    if deal_type:
        qs = qs.filter(deal_type=deal_type)

    usage_type = request.GET.get("usage_type", "").strip()
    if usage_type:
        qs = qs.filter(usage_type=usage_type)

    property_type = request.GET.get("property_type", "").strip()
    if property_type:
        qs = qs.filter(property_type=property_type)

    city = request.GET.get("city", "").strip()
    if city:
        qs = qs.filter(city__icontains=city)

    min_area = _to_int(request.GET.get("min_area"))
    if min_area is not None:
        qs = qs.filter(area__gte=min_area)

    max_area = _to_int(request.GET.get("max_area"))
    if max_area is not None:
        qs = qs.filter(area__lte=max_area)

    property_choices_grouped = [
        (
            "مسکونی",
            [
                (Property.PT_APARTMENT, "آپارتمان"),
                (Property.PT_HOUSE_VILLA, "خانه و ویلا"),
                (Property.PT_LAND_OLD, "زمین و ملک کلنگی"),
            ],
        ),
        (
            "اداری تجاری",
            [
                (Property.PT_OFFICE, "دفترکار، اتاق اداری، مطب"),
                (Property.PT_SHOP, "مغازه و غرفه"),
                (Property.PT_INDUSTRIAL, "صنعتی، کشاورزی، تجاری"),
            ],
        ),
    ]

    paginator = Paginator(qs, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "properties": page_obj.object_list,
        "page_obj": page_obj,
        "deal_choices": Property.DEAL_CHOICES,
        "usage_choices": Property.USAGE_CHOICES,
        "property_choices_grouped": property_choices_grouped,
        "filters": request.GET,
        "count": paginator.count,
    }
    return render(request, "listings/list.html", context)


def property_detail(request, pk):
    # لینک مستقیم همه وضعیت‌ها را برای مشاهده آرشیو می‌پذیرد.
    prop = get_object_or_404(
        Property.objects.prefetch_related("images", "videos"),
        pk=pk,
    )

    media_items = []
    for img in prop.images.all():
        media_items.append(
            {
                "type": "image",
                "url": img.image.url,
                "caption": img.caption or "",
            }
        )

    for vid in prop.videos.all():
        if vid.video_file:
            media_items.append(
                {
                    "type": "video",
                    "url": vid.video_file.url,
                    "caption": vid.title or "",
                    "poster": vid.poster.url if vid.poster else "",
                }
            )
        elif vid.video_url:
            media_items.append(
                {
                    "type": "video_url",
                    "url": vid.video_url,
                    "caption": vid.title or "",
                    "poster": vid.poster.url if vid.poster else "",
                }
            )

    return render(
        request,
        "listings/detail.html",
        {
            "property": prop,
            "media_items": media_items,
        },
    )


def contact_page(request):
    form = TicketForm(request.POST or None)

    if request.method == "POST":
        # Honeypot ساده برای کاهش ارسال‌های خودکار؛ جایگزین rate limiting نیست.
        if request.POST.get("website"):
            return redirect("listings:contact")

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "تیکت شما با موفقیت ارسال شد. به‌زودی با شما تماس می‌گیریم.",
            )
            return redirect("listings:contact")

        messages.error(request, "لطفاً خطاهای فرم را بررسی و اصلاح کنید.")
        return render(
            request,
            "listings/contact.html",
            {"ticket_form": form},
            status=400,
        )

    return render(request, "listings/contact.html", {"ticket_form": form})
