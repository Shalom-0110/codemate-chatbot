from django.urls import path
from .views import ask, index

urlpatterns = [
    path('', index, name='index'),  # optional for testing old HTML
    path('ask/', ask, name='ask'),
]
