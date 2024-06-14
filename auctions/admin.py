from django.contrib import admin

from .models import Auction, Bid, Category, Comment, Watchlist, User

class AuctionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "category", "price", "current_bid", "status")

class BidAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "auction", "amount")

class CommentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "auction", "date")

class WatchlistAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "auction")

class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "username", "email", "date_joined")

# Register your models here.
admin.site.register(Auction, AuctionAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(Category)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Watchlist, WatchlistAdmin)
admin.site.register(User, UserAdmin)
