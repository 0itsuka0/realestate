from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect

from .models import Property, Ticket


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

    media_items = []
    for img in prop.images.all():
        media_items.append({
            'type': 'image',
            'url': img.image.url,
            'caption': img.caption or '',
        })
    for vid in prop.videos.all():
        if vid.video_file:
            media_items.append({
                'type': 'video',
                'url': vid.video_file.url,
                'caption': vid.title or '',
                'poster': vid.poster.url if vid.poster else '',
            })
        elif vid.video_url:
            media_items.append({
                'type': 'video_url',
                'url': vid.video_url,
                'caption': vid.title or '',
                'poster': vid.poster.url if vid.poster else '',
            })

    return render(request, 'listings/detail.html', {
        'property': prop,
        'media_items': media_items,
    })


def contact_page(request):
    if request.method == 'POST':
        # هانی‌پات: اگر این فیلد مخفی پر شود، ربات است
        if request.POST.get('website'):
            return redirect('listings:contact')

        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message_text = request.POST.get('message', '').strip()

        if not (name and phone and subject and message_text):
            messages.error(request, 'لطفاً همهٔ فیلدهای ستاره‌دار را پر کنید.')
            return redirect('listings:contact')

        Ticket.objects.create(
            name=name, phone=phone, email=email,
            subject=subject, message=message_text,
        )
        messages.success(request, 'تیکت شما با موفقیت ارسال شد. به‌زودی با شما تماس می‌گیریم.')
        return redirect('listings:contact')

    return render(request, 'listings/contact.html')