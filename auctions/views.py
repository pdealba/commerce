from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.contrib import messages
from urllib.parse import urlparse

from .models import User, Category, Auction, Watchlist, Bid, Comment


def retrieve_and_clear_message(request, message_key):
    message = request.session.get(message_key)  # Retrieve error from session
    if message:
        # Clear the error from the session after retrieving it
        del request.session[message_key]
    return message


def context_processor(request):
    categories = Category.objects.all()
    return { "categories": categories }


def index(request):
    return render(request, "auctions/index.html", {
        "auctions": Auction.objects.filter(status=True) # Get all auctions that are active
    })


def login_view(request):
    if request.method == "POST":
        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")


def create_listing(request):
    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        image = request.POST["image"]
        price = request.POST["price"]

        if 'category' not in request.POST:
            request.session['error'] = "Please select a Category"
            return HttpResponseRedirect(reverse("create_listing"))
        else:
            category = request.POST["category"]

        # Validate user
        try:
            user = User.objects.get(pk=request.user.id)
            category = Category.objects.get(name=category)
        except (User.DoesNotExist, Category.DoesNotExist):
            user = category = None

        if title and description and category and price and user and category:
            new_auction = Auction(
                title=title,
                description=description,
                category=category,
                image=image,
                price=price,
                current_bid=price,
                user=user
            )
            new_auction.save()
            request.session['success'] = "Your auction has been successfully created."
            return HttpResponseRedirect(reverse("show_listing", kwargs={"auction_id": new_auction.id}))

        else:
            request.session['error'] = "Please fill out all required fields correctly: Title, Description, Category, Image URL, and Price."

    categories = Category.objects.all()

    error = retrieve_and_clear_message(request, 'error')

    return render(request, "auctions/create_listing.html", {"categories": categories, "error": error})


def show_listing(request, auction_id):
    try:
        auction = Auction.objects.get(pk=auction_id)
    except Auction.DoesNotExist:
        return HttpResponseRedirect(reverse("index"))

    # Get all comments from the auction
    usr_comments = Comment.objects.filter(auction=auction).order_by('-date')  # order them by newest to oldest

    if request.method == "POST":
        comment = request.POST["comment"]
        if comment and auction.status:
            new_comment = Comment(
                comment=comment, user=request.user,  auction=auction)
            new_comment.save()

    try:
        item_in_watchlist = Watchlist.objects.filter(user=request.user, auction=auction) # Check if the user already has the auction in watchlist to show the correct form
    except TypeError:
        item_in_watchlist = None



    error = retrieve_and_clear_message(request, 'error')
    success = retrieve_and_clear_message(request, 'success')

    return render(request, "auctions/show_listing.html", {
        "auction": auction,
        "usr_comments": usr_comments,
        "item_in_watchlist": item_in_watchlist,
        "error": error,
        "success": success
        })


def close_listing(request, auction_id):
    if request.method == "POST":
        auction = Auction.objects.get(pk=auction_id)

        # Close the auction
        auction.status = False
        auction.save()

        # Determine winner
        winner = Bid.objects.filter(
            auction=auction).order_by("-amount").first()
    if winner is not None:
        auction.winner = winner.user
        auction.save()

    return HttpResponseRedirect(reverse("show_listing", kwargs={"auction_id": auction_id}))


def watchlist(request):
    user = request.user
    if request.method == "POST":
        auction_id = request.POST["auction_id"]
        action = request.POST["action"]

        auction = Auction.objects.get(pk=auction_id)

        # We check if the watchlist already exists
        try:
            watchlist = Watchlist.objects.get(user=user, auction=auction)
        except Watchlist.DoesNotExist:
            watchlist = None

        show_listing_url = reverse("show_listing", kwargs={"auction_id": auction_id}) # Get the listing page of the item we are removing

        if action == "add":  # If the user adds the item to their watchlist
            if watchlist is None:  # We only procced if it dosent exist to prevent duplicates
                new_watchlist = Watchlist(user=user, auction=auction)
                new_watchlist.save()
                request.session["success"] = f"'{auction.title}' has been added to your watchlist."
                return HttpResponseRedirect(show_listing_url)

        elif action == "remove":  # If the user removes an item from their watchlist
            if watchlist:  # We only procced if it does exist
                watchlist.delete()
                request.session["success"] = f"'{auction.title}' has been removed from your watchlist."

                referer_path = urlparse(request.META.get('HTTP_REFERER')).path # Get the path from were the user made the post request from

                if referer_path == show_listing_url: # If the user came from the show_listing page, we rederict him back to the show_listing page
                    return HttpResponseRedirect(show_listing_url)

    usr_watchlist = Watchlist.objects.filter(user=user) # Get all of the users watchlist entries
    usr_watchlist_auctions = [entry.auction for entry in usr_watchlist] # We create an array and populate each index with the data of each auction

    success = retrieve_and_clear_message(request, 'success')
    return render(request, "auctions/watchlist.html", {"watchlist": usr_watchlist_auctions, "success": success})


def make_bid(request, auction_id):
    if request.method == "POST":
        bid = int(request.POST["bid"])

        # Check if the auction exists
        try:
            auction = Auction.objects.get(pk=auction_id)
        except Auction.DoesNotExist:
            return HttpResponseRedirect(reverse("index"))

        # If the auction is closed we prevent the user from bidding
        if auction.status == False:
            request.session['error'] = "Unable to place bid as the auction has already closed."
            return HttpResponseRedirect(reverse("show_listing", kwargs={"auction_id": auction_id}))

        # Check if bid is smaller than the current highest bid
        if bid < auction.current_bid:
            request.session['error'] = f"Unable to place your bid ($ {bid}) as amount is lower than the current highest bid ($ {auction.current_bid})."
            return HttpResponseRedirect(reverse("show_listing", kwargs={"auction_id": auction_id}))

        # Add new bid to the database
        user = request.user
        new_bid = Bid(amount=bid, user=user, auction=auction)
        new_bid.save()

        # Update current_bid and total_bids in Auction
        auction.current_bid = bid
        auction.total_bids += 1
        auction.save()

        request.session['success'] = "Your bid was successfully placed!"

    return HttpResponseRedirect(reverse("show_listing", kwargs={"auction_id": auction_id}))


def categories(request):
    return render(request, "auctions/categories.html", {"categories": Category.objects.all()})


def show_category_auctions(request, category_name):
    category = Category.objects.get(name=category_name)
    filtered_auctions = Auction.objects.filter(category=category, status=True)

    return render(request, "auctions/show_category_auctions.html", {"auctions": filtered_auctions, "category": category_name})
