from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from .models import *
from django.contrib.auth.decorators import login_required
from .forms import ChangePasswordForm
from django.contrib import messages
from django.conf import settings

# Create your views here.


@login_required(login_url='accounts:login')
def dashboard(request):
    user = request.user
    transactions = Transaction.objects.filter(account=request.user.account).order_by('-created_at')[:2]
    time = timezone.now()
    context = {
        'user': user,
        'transactions': transactions,
        'time': time
    }
    return render(request, 'User/dashboard.html', context)


@login_required(login_url='accounts:login')
def setting(request):
    user = request.user
    if request.method == 'POST':
        form = ChangePasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Password has been reset")
            return redirect('accounts:login')
        else:
            for error in list(form.errors.values()):

                messages.error(request, error)
    else:
        form = ChangePasswordForm(user)
    context = {'form': form}
    return render(request, 'User/settings.html', context)

@login_required(login_url='accounts:login')
def makeTransfer(request):
    return render(request, 'Transact/transfer.html')


@login_required(login_url='accounts:login')
def history(request):
    transfers = Transaction.objects.filter(account=request.user.account).order_by('-created_at')

    paginator = Paginator(transfers, 30)  # 20 per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'User/history.html', context)


@login_required(login_url='accounts:login')
def cards(request):
    if 'add_card' in request.GET:
        verifiedOrNot(request)
        return redirect('app:cards')
    context = {}
    return render(request, 'User/cards.html', context)


@login_required(login_url='accounts:login')
def verifiedOrNot(request):
    if not request.user.is_verified:
        return messages.warning(request, 'Account not Verified.')
    else:
        return messages.success(request, 'Card request submitted.')


@login_required(login_url='accounts:login')
def products(request):
    if 'rates' in request.GET:
        verifiedOrNot(request)
        return redirect('app:products')
    context = {}
    return render(request, 'User/products.html', context)


@login_required(login_url='accounts:login')
def loans(request):
    context = {}
    return render(request, 'User/loans.html', context)

def create_notification(
    user: User,
    notification_type: str,
    title: str,
    message: str,
    transaction: Transaction | None = None,
) -> Notification:
    """
    Create and return a Notification instance.

    Args:
        user:              The User to notify.
        notification_type: One of Notification.NotificationType values
                           e.g. "TRANSACTION", "SECURITY", "SYSTEM", "PROMOTION".
        title:             Short heading for the notification.
        message:           Full notification body.
        transaction:       Optional related Transaction instance.

    Returns:
        The newly created Notification.

    Raises:
        ValueError: If notification_type is not a valid choice.
    """
    if notification_type not in Notification.NotificationType.values:
        raise ValueError(
            f"Invalid notification_type '{notification_type}'. "
            f"Valid choices: {Notification.NotificationType.values}"
        )

    return Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        transaction=transaction,
    )

@login_required(login_url='accounts:login')
def notificationList(request):
    notifs = Notification.objects.filter(user=request.user)[:20]
    if 'read' in request.GET:
        notifs.update(is_read=True)
    context = {
        'notifs': notifs
    }
    return render(request, 'User/notifications.html', context)


def deposit(request):
    account = get_object_or_404(Account, id=request.user.account.id)
    recents = Transaction.objects.filter(account=request.user.account, transaction_type="DEPOSIT")[:4]
    context = {
        'account': account,
        'flw_public_key': settings.FLW_PUBLIC_KEY,
        'recents': recents
    }
    return render(request, 'User/deposit.html', context)


@login_required
def success(request):
    amount = request.GET.get("amount")
    tx_ref = request.GET.get("tx_ref")
    context = {
        "amount": amount,
        "tx_ref": tx_ref,
    }
    return render(request, 'Transact/success.html', context)


@login_required
def failed(request):
    context = {}
    return render(request, 'Transact/failed.html', context)


