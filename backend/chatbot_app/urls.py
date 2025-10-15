from django.urls import path
from .views import index, ask

urlpatterns = [
    path('', index, name='home'),
    path('ask/', ask, name='ask'),
]
