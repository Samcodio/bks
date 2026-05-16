from django.db import models

class Deposit(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
    ]

    transaction_id = models.CharField(max_length=100, unique=True)
    tx_ref         = models.CharField(max_length=100, unique=True)
    amount         = models.DecimalField(max_digits=12, decimal_places=2)
    currency       = models.CharField(max_length=10, default='USD')
    customer_email = models.EmailField()
    customer_name  = models.CharField(max_length=200)
    status         = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at     = models.DateTimeField(auto_now_add=True)
    verified_at    = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.customer_name} — {self.amount} {self.currency} — {self.status}"