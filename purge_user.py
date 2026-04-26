import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from users.models import User, EmailOTP, AccessToken

email = 'biku23aiml@cmrit.ac.in'
print(f"--- Purging {email} ---")

# Delete Users
users = User.objects.filter(username=email)
count = users.count()
users.delete()
print(f"Deleted {count} users.")

# Delete OTPs
otps = EmailOTP.objects.filter(email=email)
count = otps.count()
otps.delete()
print(f"Deleted {count} OTPs.")

# Delete Access Tokens
tokens = AccessToken.objects.filter(assigned_email=email)
count = tokens.count()
tokens.delete()
print(f"Deleted {count} assigned tokens.")

# Reset specifically the token the user is using if it exists
token_prefix = 'atk_TPApPu1y' # from 'atk_TPApPu1ym844wtlrR07IqMFTJAU6uylR'
AccessToken.objects.filter(token_prefix=token_prefix).update(used_at=None, used_by_email=None, is_active=True)
print(f"Reset token starting with {token_prefix}")

print("--- Purge Complete ---")
