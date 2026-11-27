# سامانه مدیریت و نمایش املاک

وب‌سایت فارسی مدیریت و نمایش فایل‌های ملکی، ساخته‌شده با Django و SQLite.

## نیازمندی‌ها

- Python سازگار با Django 6.1
- pip
- وابستگی‌های فهرست‌شده در `requirements.txt`

## راه‌اندازی محیط توسعه

در ریشه پروژه:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

فایل `.env` را باز کنید و `DJANGO_SECRET_KEY` را با یک کلید تصادفی مخصوص محیط خود جایگزین کنید. فایل `.env` در Git نادیده گرفته می‌شود و نباید Commit شود.

برای ساخت کلید محلی می‌توانید اجرا کنید:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

## آماده‌سازی دیتابیس و اجرا

```bash
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

وب‌سایت در `http://127.0.0.1:8000/` و پنل مدیریت در `http://127.0.0.1:8000/admin/` در دسترس است.

## اجرای تست‌ها

```bash
python manage.py test
python manage.py makemigrations --check --dry-run
```

## فایل‌های رسانه

تصاویر و ویدئوهای آپلودشده در مسیر `MEDIA_ROOT` (به‌صورت پیش‌فرض پوشه `media/`) ذخیره می‌شوند. این فایل‌ها و دیتابیس محلی نباید در Git قرار گیرند. در محیط Production، فایل‌های رسانه را با سرویس ذخیره‌سازی و وب‌سرور مناسب ارائه کنید.

## پیکربندی Production

در محیط انتشار، متغیرهای زیر را از طریق سرویس مدیریت Secrets/Environment تنظیم کنید:

- `DJANGO_DEBUG=False`
- `DJANGO_SECRET_KEY`: کلید قوی و محرمانه
- `DJANGO_ALLOWED_HOSTS`: فهرست دامنه‌های واقعی، جداشده با کاما
- `DJANGO_CSRF_TRUSTED_ORIGINS`: مبدأهای HTTPS مورد اعتماد، در صورت نیاز
- `DJANGO_SECURE_SSL_REDIRECT=True`: فقط وقتی HTTPS در وب‌سرور/Reverse Proxy به‌درستی فعال است
- `DJANGO_SECURE_HSTS_SECONDS`: فقط پس از اطمینان از عملکرد پایدار HTTPS

SQLite برای استقرار کم‌حجم قابل استفاده است؛ برای چندین کاربر هم‌زمان یا رشد جدی، قبل از Production درباره PostgreSQL و پشتیبان‌گیری منظم تصمیم بگیرید.

## معماری فعلی

- `config/`: تنظیمات و URLهای اصلی Django
- `listings/models.py`: مدل‌های ملک، رسانه، نقش‌ها، تنظیمات، تماس و تیکت
- `listings/views.py`: منطق نمایش فهرست، جزئیات و فرم تماس
- `listings/admin.py`: پنل مدیریت و نقش‌های مدیریتی
- `templates/listings/`: قالب‌های HTML
- `static/`: CSS، JavaScript، فونت و Bootstrap

## نکات عملیاتی

- فایل‌های `db.sqlite3.bak*` که ممکن است قبلاً Commit شده باشند، صرفاً با اضافه‌شدن الگو به `.gitignore` از تاریخچه Git حذف نمی‌شوند. پیش از حذف آن‌ها باید محتوایشان از نظر وجود داده شخصی بررسی و برای حذف تاریخچه، تصمیم جداگانه گرفته شود.
- ارسال ایمیل تیکت‌ها هنوز پیکربندی نشده است. برای فعال‌سازی آن به SMTP/Email provider و متغیرهای محرمانه محیط نیاز است.
- قبل از اجرای Migrationها روی دیتابیس واقعی، از دیتابیس و فایل‌های رسانه نسخه پشتیبان بگیرید.
