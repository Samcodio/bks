import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bks.settings")
django.setup()

from django.contrib.auth import get_user_model
from app.models import Country

User = get_user_model()

if not User.objects.filter(username="admin2").exists():
    User.objects.create_superuser(
        username="admin2",
        email="administa@gmail.com",
        password="@Syntax2000"
    )
    print("Superuser created")
else:
    print("Superuser already exists")


# Populate countries table
countries_data = [
    ("United States", "$"), ("United Kingdom", "£"), ("Nigeria", "₦"),
    ("Canada", "$"), ("Australia", "$"), ("Germany", "€"), ("France", "€"),
    ("Italy", "€"), ("Spain", "€"), ("Netherlands", "€"), ("Belgium", "€"),
    ("Ireland", "€"), ("Portugal", "€"), ("Austria", "€"), ("Greece", "€"),
    ("Switzerland", "CHF"), ("Sweden", "kr"), ("Norway", "kr"), ("Denmark", "kr"),
    ("Finland", "€"), ("Poland", "zł"), ("Russia", "₽"), ("Ukraine", "₴"),
    ("Turkey", "₺"), ("India", "₹"), ("China", "¥"), ("Japan", "¥"),
    ("South Korea", "₩"), ("Indonesia", "Rp"), ("Malaysia", "RM"),
    ("Singapore", "$"), ("Thailand", "฿"), ("Vietnam", "₫"), ("Philippines", "₱"),
    ("Pakistan", "₨"), ("Bangladesh", "৳"), ("Sri Lanka", "₨"),
    ("South Africa", "R"), ("Egypt", "£"), ("Kenya", "KSh"), ("Ghana", "₵"),
    ("Morocco", "MAD"), ("Algeria", "DA"), ("Ethiopia", "Br"), ("Tanzania", "TSh"),
    ("Uganda", "USh"), ("Cameroon", "FCFA"), ("Ivory Coast", "CFA"),
    ("Senegal", "CFA"), ("Zambia", "ZK"), ("Zimbabwe", "$"), ("Rwanda", "FRw"),
    ("Brazil", "R$"), ("Argentina", "$"), ("Mexico", "$"), ("Chile", "$"),
    ("Colombia", "$"), ("Peru", "S/"), ("Venezuela", "Bs"), ("Ecuador", "$"),
    ("Uruguay", "$"), ("Bolivia", "Bs"), ("Paraguay", "₲"),
    ("United Arab Emirates", "د.إ"), ("Saudi Arabia", "﷼"), ("Qatar", "﷼"),
    ("Kuwait", "د.ك"), ("Bahrain", ".د.ب"), ("Oman", "﷼"), ("Israel", "₪"),
    ("Jordan", "د.ا"), ("Lebanon", "ل.ل"), ("Iraq", "ع.د"), ("Iran", "﷼"),
    ("New Zealand", "$"), ("Fiji", "$"), ("Papua New Guinea", "K"),
    ("Czech Republic", "Kč"), ("Hungary", "Ft"), ("Romania", "lei"),
    ("Bulgaria", "лв"), ("Croatia", "€"), ("Serbia", "дин"), ("Slovakia", "€"),
    ("Slovenia", "€"), ("Iceland", "kr"), ("Luxembourg", "€"), ("Malta", "€"),
    ("Cyprus", "€"), ("Estonia", "€"), ("Latvia", "€"), ("Lithuania", "€"),
    ("Hong Kong", "$"), ("Taiwan", "NT$"), ("Nepal", "₨"), ("Myanmar", "K"),
    ("Cambodia", "៛"), ("Laos", "₭"), ("Mongolia", "₮"), ("Kazakhstan", "₸"),
    ("Uzbekistan", "so'm"), ("Afghanistan", "؋"),
]

for name, symbol in countries_data:
    Country.objects.get_or_create(name=name, defaults={"currency_symbol": symbol})

print(f"Total countries in DB: {Country.objects.count()}")