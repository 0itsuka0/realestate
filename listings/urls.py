from django.urls import path
from . import views

app_name = 'listings'

urlpatterns = [
    path('', views.property_list, name='list'),
    path('property/<int:pk>/', views.property_detail, name='detail'),
    path('contact/', views.contact_page, name='contact'),
]