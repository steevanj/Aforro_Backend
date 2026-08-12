from django.urls import include, path


urlpatterns = [

    path(
        "",
        include("orders.urls")
    ),

    path(
        "",
        include("stores.urls")
    ),
    path(
        "",
        include("search.urls")
    ),
]