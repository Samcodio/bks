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
    raw = request.GET.get("response")  # 👈 this is where everything is

    if not raw:
        return redirect("app:failed")

    # decode and parse the JSON
    data = json.loads(unquote(raw))

    print("Flutterwave data:", data)  # confirm it works

    status         = data.get("status")
    transaction_id = data.get("id")        # note: "id" not "transaction_id"
    tx_ref         = data.get("txRef")     # note: "txRef" not "tx_ref"
    currency       = data.get("currency")
    amount         = data.get("amount")

    if status == "successful" and transaction_id and currency == "USD":
        # verify with Flutterwave API
        url = f"https://api.flutterwave.com/v3/transactions/{transaction_id}/verify"
        headers = {"Authorization": f"Bearer {settings.FLW_SECRET_KEY}"}
        response = requests.get(url, headers=headers)
        verified = response.json()

        if verified.get("status") == "success":
            tx = verified["data"]

            if tx["status"] == "successful" and tx["currency"] == "USD":
                # credit account
                account = request.user.account
                inital_bal = account.balance
                account.balance += tx["amount"]
                account.save()

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
                Transaction.objects.get_or_create(
                    account=request.user.account,
                    transaction_type="DEPOSIT",
                    amount=tx["amount"],
                    balance_before=inital_bal,
                    balance_after=account.balance,
                    description="FL/Card",
                    reference=tx["tx_ref"],
                    status="COMPLETED",
                )

                return redirect(
                    f"{reverse('app:success')}?amount={tx['amount']}&tx_ref={tx['tx_ref']}"
                )

    return redirect("app:failed")
