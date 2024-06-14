from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create/listing", views.create_listing, name="create_listing"),
    path("listing/<int:auction_id>", views.show_listing, name="show_listing"),
    path("close/listing/<int:auction_id>", views.close_listing, name="close_listing"),
    path("watchlist", views.watchlist, name="watchlist"),
    path("make-a-bid/<int:auction_id>", views.make_bid, name="make_bid"),
    path("categories", views.categories, name="categories"),
    path("category/<str:category_name>", views.show_category_auctions, name="show_category_auctions"),
]
