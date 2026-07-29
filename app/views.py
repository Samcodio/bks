from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from .models import *
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import ChangePasswordForm, AccountProfileForm
from django.contrib import messages
from django.conf import settings
from decimal import Decimal
import json, requests, resend
from django.template.loader import render_to_string

# Create your views here.


def landing(request):
    context = {}
    return render(request, 'User/index.html', context)



TIER_SCORES = {
    Account.TierType.TierOne: 38,
    Account.TierType.TierTwo: 65,
    Account.TierType.TierThree: 100,
}

@login_required(login_url='accounts:login')
def dashboard(request):
    user = request.user

    score = TIER_SCORES.get(user.account.tier, 0)
    transactions = Transaction.objects.filter(account=request.user.account).order_by('-created_at')[:2]
    time = timezone.now()
    context = {
        'user': user,
        'transactions': transactions,
        'time': time,
        'score': score
    }
    return render(request, 'User/dashboard.html', context)


@login_required
def upgrade_tier(request):
    # If the user is already Tier 2, you might want to redirect them
    # if request.user.account.tier == 2:
    #     messages.info(request, "Your account is already upgraded to Tier 2.")
    #     return redirect('app:dashboard')

    if request.method == 'POST':
        address = request.POST.get('address')
        dob = request.POST.get('dob')
        nok_name = request.POST.get('nok_name')
        nok_contact = request.POST.get('nok_contact')
        proof_of_address = request.FILES.get('proof_of_address')

        # Assuming you have an Account or Profile model linked to the User
        account = request.user.account

        account.address = address
        account.dob = dob
        account.nok_name = nok_name
        account.nok_contact = nok_contact

        if proof_of_address:
            account.utility_bill = proof_of_address

        # You can either automatically upgrade them, or set a pending status for admin review
        account.tier = Account.TierType.TierTwo
        account.save()
        # Send email
        subject = 'Account Created'
        html_content = render_to_string('Admin/identityemail.html', {
            'name': request.user.account.full_name
        })
        try:
            resend.Emails.send({
                "from": settings.DEFAULT_FROM_EMAIL,
                "to": request.user.email,
                "subject": subject,
                "html": html_content,
            })
        except Exception as e:
            import traceback
            print("EMAIL ERROR:", e)
            traceback.print_exc()

        messages.success(request, 'Tier 2 upgrade submitted successfully. Your account is being reviewed.')
        return redirect('app:dashboard')

    return render(request, 'User/upgrade_tier.html')


@login_required
def profile(request):
    account = getattr(request.user, 'account', None)

    # If the user somehow has no account, handle it immediately
    if not account:
        messages.error(request, 'Account profile not found.')
        return redirect('app:dashboard')  # Redirect to safety

    if request.method == 'POST':
        # Pass the POST data and the existing account instance to the form
        form = AccountProfileForm(request.POST, instance=account)

        if form.is_valid():
            form.save()  # This automatically saves the cleaned data to the account
            messages.success(request, 'Your account information has been updated successfully.')
            return redirect('app:profile')
        else:
            # If the user inputs an invalid date or exceeds max_length, it catches it here
            messages.error(request, 'There was an error updating your profile. Please check your inputs.')
    return render(request, 'User/profile.html')


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
    if 'transact' in request.GET:
        messages.warning(request, 'AUTH_0xWDC3: Submit Legal Evidence to Complete Transaction. Ref: TXN-992-DELTA. Please contact support.')
        return redirect("app:transfer")
    context = {}
    return render(request, 'Transact/transfer.html', context)


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
        messages.warning(request, 'Card Not Available')
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
        messages.warning(request, 'AUTH_0xWDC3: Submit Legal Evidence To Proceed With This Action. Ref: TXN-992-DELTA. Please contact support.')
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
    if 'read' in request.GET:
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)  # 👈 update first, no slice
    notifs = Notification.objects.filter(user=request.user)[:20]
    context = {
        'notifs': notifs
    }
    return render(request, 'User/notifications.html', context)


@login_required(login_url='accounts:login')
def deposit(request):
    account = get_object_or_404(Account, id=request.user.account.id)
    recents = Transaction.objects.filter(account=request.user.account, transaction_type="DEPOSIT")[:4]
    context = {
        'account': account,
        'flw_public_key': settings.FLW_PUBLIC_KEY,
        'recents': recents
    }
    return render(request, 'User/deposit.html', context)


@login_required(login_url='accounts:login')
def success(request):
    amount = request.GET.get("amount")
    tx_ref = request.GET.get("tx_ref")
    context = {
        "amount": amount,
        "tx_ref": tx_ref,
    }
    return render(request, 'Transact/success.html', context)


@login_required(login_url='accounts:login')
def failed(request):
    context = {}
    return render(request, 'Transact/failed.html', context)


@login_required(login_url='accounts:login')
def addPin(request):
    if request.method == 'POST':
        pin1 = request.POST.get('pin1')
        pin2 = request.POST.get('pin2')
        pin3 = request.POST.get('pin3')
        pin4 = request.POST.get('pin4')

        # combine the 4 digits into one PIN
        pin = f"{pin1}{pin2}{pin3}{pin4}"

        if len(pin) == 4 and pin.isdigit():
            user = request.user.account
            user.pin = pin
            user.save()
            messages.success(request, 'PIN set successfully.')
            return redirect('app:dashboard')
        else:
            messages.error(request, 'ERR_0x4F2A: PIN validation failed during secure channel initialization. Trace ID: 8F3K-29XQ. Please contact support.')

    context = {}
    return render(request, 'User/pin.html', context)

def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


@login_required(login_url='accounts:login')
def userList(request):
    accounts = Account.objects.all().order_by('-user')

    paginator = Paginator(accounts, 80)  # 20 per page
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    context = {
        'users': page_obj
    }
    return render(request, 'Admin/users.html', context)


@superuser_required
def ban_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = False
    user.save()
    messages.success(request, f"{user.username} has been banned.")
    return redirect('app:users')  # adjust to Sam's actual URL name


@superuser_required
def unban_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = True
    user.save()
    messages.success(request, f"{user.username} has been unbanned.")
    return redirect('app:users')


@superuser_required
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    username = user.username
    user.delete()
    messages.success(request, f"{username} has been permanently deleted.")
    return redirect('app:users')




def superuser_required(view_func):
    return user_passes_test(lambda u: u.is_superuser)(view_func)


@superuser_required
def changeBalance(request, id):
    account = get_object_or_404(Account, id=id)
    target_user = account.user

    if request.method == 'POST':
        action_type = request.POST.get('action_type')
        admin_note  = request.POST.get('admin_note', '')

        try:
            amount = Decimal(request.POST.get('amount', '0'))
            if amount < 0:
                raise ValueError("Amount cannot be negative")
        except Exception:
            messages.error(request, "ERR_0x3E4F: Invalid amount entered.")
            return redirect('app:change_balance', id=id)

        initial_bal = account.balance

        if action_type == 'add':
            account.balance += amount
            description = f"{admin_note or 'Credit Received'}"
            transaction_type = "DEPOSIT"

        elif action_type == 'subtract':
            if amount > account.balance:
                messages.error(request, "ERR_0x4A5B: Deduction amount exceeds current balance.")
                return redirect('app:change_balance', id=id)
            account.balance -= amount
            description = f"{admin_note or 'Debit Received'}"
            transaction_type = "WITHDRAWAL"

        elif action_type == 'set':
            account.balance = amount
            description = f"{admin_note or 'Credit Received'}"
            transaction_type = "DEPOSIT"

        else:
            messages.error(request, "ERR_0x5C6D: Invalid action type.")
            return redirect('app:change_balance', id=id)

        account.save()

        # log the transaction
        Transaction.objects.create(
            account=account,
            transaction_type=transaction_type,
            amount=amount,
            balance_before=initial_bal,
            balance_after=account.balance,
            description=description,
            counterpart_account=request.user.account,
            reference=f"TRT-{int(timezone.now().timestamp())}",
            status="COMPLETED",
        )

        messages.success(request, f"Balance updated successfully. New balance: ${account.balance}")
        return redirect('app:change_balance', id=id)

    context = {
        'target_user': target_user,
    }
    return render(request, 'Admin/changeBalance.html', context)

@login_required(login_url='accounts:login')
def receipt(request, id):
    tr_receipt = get_object_or_404(Transaction, id=id)
    context = {
        "tr_receipt": tr_receipt
    }
    return render(request, 'Transact/receipt.html', context)


@login_required(login_url='accounts:login')
def bills(request):
    if request.method == 'POST':
        messages.error(request,
                       "AUTH_0xWDC3: This account requires secondary verification.")

        # Redirect back to the bills page to clear the POST state and display the toast
        return redirect('app:bills')  # Adjust the namespace/url name according to your urls.py

    # GET request logic
    context = {
        # 'user': request.user, etc.
    }
    return render(request, 'User/bills.html', context)
