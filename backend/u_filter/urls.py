from django.urls import path
from .views import HelloView,  BERTView

urlpatterns = [
    path("hello/", HelloView.as_view(), name="hello"),
]

urlpatterns = [
    path("bert/", BERTView.as_view(), name="bert"),
]