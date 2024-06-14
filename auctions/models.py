from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    pass


class Category(models.Model):
    name = models.CharField(max_length=64)

    def __str__(self):
        return f"{self.name}"


class Auction(models.Model):
    title = models.CharField(max_length=64)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="category")
    image = models.URLField(blank=True)
    price = models.DecimalField(max_digits=9, decimal_places=2)
    current_bid = models.DecimalField(max_digits=9, decimal_places=2)
    total_bids = models.IntegerField(default=0)
    status = models.BooleanField(default=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user")
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="won_auction")
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title}"


class Bid(models.Model):
    amount = models.DecimalField(max_digits=9, decimal_places=2)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bidder")
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="bid_origin")

    def __str__(self):
        return f"({self.user}) placed a bid of ${self.amount} in {self.auction}"


class Comment(models.Model):
    comment = models.TextField()
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="commenter")
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="comment_origin")
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comment from {self.auction} by {self.user}: {self.comment} ({self.date})"


class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="watchlist_user")
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name="watchlist_auction")

    def __str__(self):
        return f"'{self.user}' has '{self.auction}' in their watchlist"
