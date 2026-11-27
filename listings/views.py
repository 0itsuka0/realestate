from django.contrib import admin, messages
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect

from .forms import OwnerAccountForm, TicketForm
from .models import Property


_DIGIT_TRANSLATION = str.maketrans(
    "۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩",
    "01234567890123456789",
)


def _normalize_digits(value):
    return str(value or "").translate(_DIGIT_TRANSLATION)


def _to_int(value):
    """Parse Persian/Arabic digits and common thousands separators safely."""
    normalized = _normalize_digits(value).replace(",", "").replace("٬", "").replace(" ", "")
    if not normalized:
        return None
    try:
        number = int(normalized)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _apply_range(queryset, field_name, minimum, maximum):
    if minimum is not None and maximum is not None and minimum > maximum:
        minimum, maximum = maximum, minimum
    if minimum is not None:
        queryset = queryset.filter(**{f"{field_name}__gte": minimum})
    if maximum is not None:
        queryset = queryset.filter(**{f"{field_name}__lte": maximum})
    return queryset


def property_list(request):
    queryset = Property.objects.filter(
        status=Property.STATUS_ACTIVE
    ).prefetch_related("images")

    # Tokenized search: every term must match at least one searchable field.
    search_query = _normalize_digits(request.GET.get("q", "")).strip()[:120]
    searchable_fields = (
        "title", "province", "city", "neighborhood",
        "address", "description", "phone",
    )
    for term in search_query.split():
        term_query = Q()
        for field in searchable_fields:
            term_query |= Q(**{f"{field}__icontains": term})
        queryset = queryset.filter(term_query)

    valid_deal_types = {value for value, _ in Property.DEAL_CHOICES}
    valid_usage_types = {value for value, _ in Property.USAGE_CHOICES}
    valid_property_types = {value for value, _ in Property.PT_CHOICES}

    deal_type = request.GET.get("deal_type", "").strip()
    if deal_type not in valid_deal_types:
        deal_type = ""
    elif deal_type:
        queryset = queryset.filter(deal_type=deal_type)

    usage_type = request.GET.get("usage_type", "").strip()
    if usage_type not in valid_usage_types:
        usage_type = ""
    elif usage_type:
        queryset = queryset.filter(usage_type=usage_type)

    property_type = request.GET.get("property_type", "").strip()
    if property_type not in valid_property_types:
        property_type = ""
    elif property_type:
        queryset = queryset.filter(property_type=property_type)

    province = request.GET.get("province", "").strip()[:100]
    city = request.GET.get("city", "").strip()[:100]
    neighborhood = request.GET.get("neighborhood", "").strip()[:100]
    if province:
        queryset = queryset.filter(province__icontains=province)
    if city:
        queryset = queryset.filter(city__icontains=city)
    if neighborhood:
        queryset = queryset.filter(neighborhood__icontains=neighborhood)

    bedrooms = _to_int(request.GET.get("bedrooms"))
    if bedrooms is not None and bedrooms <= 20:
        queryset = queryset.filter(bedrooms__gte=bedrooms)

    # Price ranges are deliberately deal-specific: sale prices are not mixed
    # with rental deposits or monthly rent.
    price_min = _to_int(request.GET.get("price_min"))
    price_max = _to_int(request.GET.get("price_max"))
    deposit_min = _to_int(request.GET.get("deposit_min"))
    deposit_max = _to_int(request.GET.get("deposit_max"))
    rent_min = _to_int(request.GET.get("rent_min"))
    rent_max = _to_int(request.GET.get("rent_max"))

    if deal_type == Property.DEAL_SALE:
        queryset = _apply_range(queryset, "price", price_min, price_max)
    elif deal_type == Property.DEAL_RENT:
        queryset = _apply_range(queryset, "deposit", deposit_min, deposit_max)
        queryset = _apply_range(queryset, "rent", rent_min, rent_max)

    # Retain support for old bookmarked URLs without showing area filters in
    # the redesigned public search form.
    min_area = _to_int(request.GET.get("min_area"))
    max_area = _to_int(request.GET.get("max_area"))
    if min_area is not None or max_area is not None:
        queryset = _apply_range(queryset, "area", min_area, max_area)

    for parameter, field_name in (
        ("has_parking", "has_parking"),
        ("has_elevator", "has_elevator"),
        ("has_storage", "has_storage"),
        ("has_balcony", "has_balcony"),
        ("is_featured", "is_featured"),
    ):
        if request.GET.get(parameter) in {"1", "true", "on"}:
            queryset = queryset.filter(**{field_name: True})

    sort = request.GET.get("sort", "newest").strip()
    if sort == "oldest":
        queryset = queryset.order_by("created_at")
    elif sort in {"price_asc", "price_desc"}:
        direction = "" if sort == "price_asc" else "-"
        if deal_type == Property.DEAL_RENT:
            queryset = queryset.order_by(
                f"{direction}deposit", f"{direction}rent", "-created_at"
            )
        else:
            queryset = queryset.order_by(f"{direction}price", "-created_at")
    else:
        sort = "newest"
        queryset = queryset.order_by("-is_featured", "-created_at")

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

    paginator = Paginator(queryset, 12)
    page_obj = paginator.get_page(request.GET.get("page"))

    context = {
        "properties": page_obj.object_list,
        "page_obj": page_obj,
        "deal_choices": Property.DEAL_CHOICES,
        "usage_choices": Property.USAGE_CHOICES,
        "property_choices_grouped": property_choices_grouped,
        "filters": request.GET,
        "count": paginator.count,
        "sort": sort,
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



@admin.site.admin_view
def owner_account(request):
    """Let only the superuser edit their own basic account details."""
    if not request.user.is_superuser:
        raise PermissionDenied

    if request.method == "POST":
        form = OwnerAccountForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "اطلاعات حساب مدیر اصلی با موفقیت ذخیره شد.")
            return redirect("owner_account")
    else:
        form = OwnerAccountForm(instance=request.user)

    context = admin.site.each_context(request)
    context.update({
        "title": "تنظیمات حساب مدیر اصلی",
        "form": form,
    })
    return render(request, "admin/owner_account.html", context)
