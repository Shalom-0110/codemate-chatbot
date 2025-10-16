from django.urls import path
from .views import index, ask, welcome

urlpatterns = [
    path("", welcome, name="welcome"),
    path("chat/", index, name="chat"),
    path('ask/', ask, name='ask'),
]
