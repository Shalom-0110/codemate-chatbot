from django.urls import path
from .views import chat, ask, welcome

urlpatterns = [
    path("", welcome, name="welcome"),
    path("chat/", chat, name="chat"),
    path('ask/', ask, name='ask'),
]
