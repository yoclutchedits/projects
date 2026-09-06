# app/utils/email.py

def send_verification_email(to_email: str, code: str):
    print("=" * 40)
    print(f"[FAKE EMAIL] To: {to_email}")
    print(f"Your verification code is: {code}")
    print("=" * 40)