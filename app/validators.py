# validators.py

from django.core.exceptions import ValidationError

def validate_mobile_number(value):
    if not value.isdigit():
        raise ValidationError("Mobile number must contain only digits.")
    if len(value) != 10:
        raise ValidationError("Mobile number must be exactly 10 digits long.")
