from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('pages.urls')),
    path('courses/', include('courses.urls')),
    path('_nested_admin/', include('nested_admin.urls')),
]