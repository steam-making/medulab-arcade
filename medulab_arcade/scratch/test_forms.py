import os
import sys
import django

# 현재 디렉토리를 파이썬 경로에 추가
sys.path.append(os.getcwd())

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'medulab_arcade.settings')
django.setup()

from arcade.forms import AdminUserForm, AdminUserProfileForm, SignUpForm
from django.contrib.auth.models import User

print("Testing forms...")
try:
    u_form = AdminUserForm()
    print("AdminUserForm instantiated.")
    up_form = AdminUserProfileForm()
    print("AdminUserProfileForm instantiated.")
    s_form = SignUpForm()
    print("SignUpForm instantiated.")
    print("All forms instantiated successfully!")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
