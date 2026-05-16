from django.shortcuts import render, redirect, reverse
import uuid
from app.models import Transaction
import requests
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import Deposit
import json
from urllib.parse import unquote


# ── 1. Initiate deposit — returns public key + tx_ref to frontend ──
def initiate_deposit(request):
    if request.method == "GET":
        tx_ref = "dep-" + str(uuid.uuid4())  # unique reference per deposit
        return JsonResponse({
            "public_key": settings.FLW_PUBLIC_KEY,
            "tx_ref": tx_ref,
            "currency": "USD",
        })


# ── 2. Verify payment — called after Flutterwave checkout completes ──
@csrf_exempt
def verify_deposit(request):
    if request.method == "POST":
        body = json.loads(request.body)
        transaction_id = body.get("transaction_id")

        if not transaction_id:
            return JsonResponse({"status": "error", "message": "No transaction ID provided"}, status=400)

        # Call Flutterwave's verify endpoint
        url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
        headers = {"Authorization": f"Bearer {settings.FLW_SECRET_KEY}"}

        response = requests.get(url, headers=headers)
        data = response.json()

        if data.get("status") != "success":
            return JsonResponse({"status": "error", "message": "Verification failed"}, status=400)

        tx_data = data["data"]

        # Validate the transaction is legitimate
        if tx_data["status"] != "successful":
            return JsonResponse({"status": "failed", "message": "Payment was not successful"})

        if tx_data["currency"] != "USD":
            return JsonResponse({"status": "error", "message": "Invalid currency"}, status=400)

        # Save or update deposit record
        deposit, created = Deposit.objects.get_or_create(
            transaction_id=str(tx_data["id"]),
            defaults={
                "tx_ref":         tx_data["tx_ref"],
                "amount":         tx_data["amount"],
                "currency":       tx_data["currency"],
                "customer_email": tx_data["customer"]["email"],
                "customer_name":  tx_data["customer"]["name"],
                "status":         "successful",
                "verified_at":    timezone.now(),
            }
        )

        # Return deposit info back to Sam's frontend
        return JsonResponse({
            "status": "success",
            "deposit": {
                "transaction_id": deposit.transaction_id,
                "tx_ref":         deposit.tx_ref,
                "amount":         str(deposit.amount),
                "currency":       deposit.currency,
                "customer_name":  deposit.customer_name,
                "customer_email": deposit.customer_email,
                "verified_at":    str(deposit.verified_at),
            }
        })


# ── 3. Webhook — Flutterwave pings this automatically on payment ──
@csrf_exempt
def flutterwave_webhook(request):
    if request.method == "POST":
        secret_hash = settings.FLW_ENCRYPTION_KEY
        signature = request.headers.get("verif-hash")

        if signature != secret_hash:
            return JsonResponse({"status": "unauthorized"}, status=401)

        payload = json.loads(request.body)

        if (payload.get("event") == "charge.completed" and
                payload["data"]["status"] == "successful" and
                payload["data"]["currency"] == "USD"):

            tx = payload["data"]
            Deposit.objects.update_or_create(
                transaction_id=str(tx["id"]),
                defaults={
                    "tx_ref":         tx["tx_ref"],
                    "amount":         tx["amount"],
                    "currency":       tx["currency"],
                    "customer_email": tx["customer"]["email"],
                    "customer_name":  tx["customer"]["name"],
                    "status":         "successful",
                    "verified_at":    timezone.now(),
                }
            )

        return JsonResponse({"status": "ok"})




def deposit_redirect(request):
    raw = request.GET.get("response")

    if not raw:
        print("FAILED: no raw response")
        return redirect("app:failed")

    try:
        data = json.loads(unquote(raw))
        print("Flutterwave data:", data)
    except Exception as e:
        print(f"FAILED: could not parse response - {e}")
        return redirect("app:failed")

    status         = data.get("status")
    transaction_id = data.get("id")
    tx_ref         = data.get("txRef")
    currency       = data.get("currency")
    amount         = data.get("amount")
    customer       = data.get("customer", {})
    email          = customer.get("email")

    print(f"status={status} | tx_id={transaction_id} | currency={currency} | tx_ref={tx_ref}")

    if status == "successful" and transaction_id and currency == "USD":
        try:
            url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
            headers = {"Authorization": f"Bearer {settings.FLW_SECRET_KEY}"}
            response = requests.get(url, headers=headers)
            verified = response.json()
            print(f"VERIFIED: {verified.get('status')}")
        except Exception as e:
            print(f"FAILED: verification request error - {e}")
            return redirect("app:failed")

        if verified.get("status") == "success":
            tx = verified["data"]
            print(f"TX STATUS: {tx['status']} | TX CURRENCY: {tx['currency']}")

            if tx["status"] == "successful" and tx["currency"] == "USD":
                from django.contrib.auth import get_user_model
                User = get_user_model()
                try:
                    user_id = tx_ref.split("-")[1]
                    print(f"USER ID: {user_id}")
                    user = User.objects.get(id=user_id)
                    account = user.account
                    inital_bal = account.balance
                    account.balance += tx["amount"]
                    account.save()
                    print(f"BALANCE UPDATED: {inital_bal} -> {account.balance}")
                except User.DoesNotExist:
                    print(f"FAILED: no user with id={user_id}")
                    return redirect("app:failed")
                except (IndexError, ValueError) as e:
                    print(f"FAILED: tx_ref parse error - {e}")
                    return redirect("app:failed")

                try:
                    Deposit.objects.get_or_create(
                        transaction_id=str(tx["id"]),
                        defaults={
                            "tx_ref":         tx["tx_ref"],
                            "amount":         tx["amount"],
                            "currency":       tx["currency"],
                            "customer_email": tx["customer"]["email"],
                            "customer_name":  tx["customer"]["name"],
                            "status":         "successful",
                            "verified_at":    timezone.now(),
                        }
                    )
                    print("DEPOSIT SAVED")
                except Exception as e:
                    print(f"FAILED: deposit save error - {e}")
                    return redirect("app:failed")

                try:
                    Transaction.objects.get_or_create(
                        account=account,
                        transaction_type="DEPOSIT",
                        amount=tx["amount"],
                        balance_before=inital_bal,
                        balance_after=account.balance,
                        description="FL/Card",
                        reference=tx["tx_ref"],
                        status="COMPLETED",
                    )
                    print("TRANSACTION SAVED")
                except Exception as e:
                    print(f"FAILED: transaction save error - {e}")
                    return redirect("app:failed")

                print("=== ALL GOOD - REDIRECTING TO SUCCESS ===")
                return redirect(
                    f"{reverse('app:success')}?amount={tx['amount']}&tx_ref={tx['tx_ref']}"
                )
        else:
            print(f"FAILED: verified status = {verified.get('status')}")
    else:
        print(f"FAILED: outer condition — status={status} | currency={currency} | tx_id={transaction_id}")

    return redirect("app:failed")
