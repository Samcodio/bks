import uuid
import random
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save
from django.dispatch import receiver



class User(AbstractUser):
    full_name = models.CharField(max_length=50, blank=True, null=True)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20, blank=True)
    is_verified   = models.BooleanField(default=False)
    social_sec = models.CharField(max_length=20)

    class Meta:
        db_table = "users"

    def __str__(self):
        return self.username


class Account(models.Model):

    class AccountType(models.TextChoices):
        SAVINGS  = "SAVINGS",  "Savings"
        CHECKING = "CHECKING", "Checking"
        WALLET   = "WALLET",   "Wallet"

    id             = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user           = models.OneToOneField(User, on_delete=models.PROTECT, related_name="account")
    account_genID  = models.CharField(max_length=20, unique=True, db_index=True)
    account_type   = models.CharField(max_length=20, choices=AccountType.choices, default=AccountType.SAVINGS)
    balance        = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    is_active      = models.BooleanField(default=True)
    created_at     = models.DateTimeField(auto_now_add=True)
    updated_at     = models.DateTimeField(auto_now=True)
    pin            = models.CharField(max_length=4, null=True, blank=True)

    class Meta:
        db_table = "accounts"

    def __str__(self):
        return f"{self.account_genID} ({self.user.username})"

    def save(self, *args, **kwargs):
        if not self.account_genID:
            self.account_genID = self._generate_unique_genid()
        super().save(*args, **kwargs)

    def _generate_unique_genid(self):
        max_attempts = 100
        for _ in range(max_attempts):
            random_digits = f"{random.randint(0, 9999999):07d}"
            gen_id = f"00{random_digits}"

            if not Account.objects.filter(account_genID=gen_id).exists():
                return gen_id

        raise RuntimeError("Error generating account id")

class Transaction(models.Model):

    class TransactionType(models.TextChoices):
        DEPOSIT    = "DEPOSIT",    "Deposit"
        WITHDRAWAL = "WITHDRAWAL", "Withdrawal"
        TRANSFER   = "TRANSFER",   "Transfer"
        REVERSAL   = "REVERSAL",   "Reversal"

    class Status(models.TextChoices):
        PENDING   = "PENDING",   "Pending"
        COMPLETED = "COMPLETED", "Completed"
        FAILED    = "FAILED",    "Failed"
        REVERSED  = "REVERSED",  "Reversed"

    id              = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    account         = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="transactions")
    transaction_type = models.CharField(max_length=20, choices=TransactionType.choices)
    amount          = models.DecimalField(max_digits=18, decimal_places=2)

    # Snapshot balances so history is self-contained — never recalculate
    balance_before  = models.DecimalField(max_digits=18, decimal_places=2)
    balance_after   = models.DecimalField(max_digits=18, decimal_places=2)

    description     = models.TextField(blank=True)
    reference       = models.CharField(max_length=100, unique=True, db_index=True)  # idempotency key
    status          = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)

    # For TRANSFER: link to the counterpart account
    counterpart_account = models.ForeignKey(
        Account,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="incoming_transfers",
    )

    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "transactions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.transaction_type} {self.amount} — {self.reference}"


class Notification(models.Model):

    class NotificationType(models.TextChoices):
        TRANSACTION = "TRANSACTION", "Transaction alert"
        SECURITY    = "SECURITY",    "Security alert"
        SYSTEM      = "SYSTEM",      "System message"
        PROMOTION   = "PROMOTION",   "Promotion"

    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user              = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    transaction       = models.ForeignKey(
        Transaction,
        null=True, blank=True,
        on_delete=models.SET_NULL,
        related_name="notifications",
    )
    notification_type = models.CharField(max_length=20, choices=NotificationType.choices)
    title             = models.CharField(max_length=255)
    message           = models.TextField()
    is_read           = models.BooleanField(default=False)
    created_at        = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} → {self.user.username}"


@receiver(post_save, sender=User)
def create_token(sender, instance, created, **kwargs):
    if created:
        Account.objects.create(user=instance)


