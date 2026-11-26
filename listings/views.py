from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from .models import Property


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def property_list(request):
    qs = Property.objects.filter(is_active=True).prefetch_related('images')

    q = request.GET.get('q', '').strip()
    if q:
        qs = qs.filter(
            Q(title__icontains=q) |
            Q(city__icontains=q) |
            Q(neighborhood__icontains=q) |
            Q(address__icontains=q) |
            Q(description__icontains=q)
        )

    deal_type = request.GET.get('deal_type', '').strip()
    if deal_type:
        qs = qs.filter(deal_type=deal_type)

    property_type = request.GET.get('property_type', '').strip()
    if property_type:
        qs = qs.filter(property_type=property_type)

    city = request.GET.get('city', '').strip()
    if city:
        qs = qs.filter(city__icontains=city)

    min_area = _to_int(request.GET.get('min_area'))
    if min_area is not None:
        qs = qs.filter(area__gte=min_area)

    max_area = _to_int(request.GET.get('max_area'))
    if max_area is not None:
        qs = qs.filter(area__lte=max_area)

    context = {
        'properties': qs,
        'deal_choices': Property.DEAL_CHOICES,
        'property_choices': Property.PROPERTY_CHOICES,
        'filters': request.GET,
        'count': qs.count(),
    }
    return render(request, 'listings/list.html', context)


def property_detail(request, pk):
    prop = get_object_or_404(Property, pk=pk, is_active=True)
    return render(request, 'listings/detail.html', {'property': prop})