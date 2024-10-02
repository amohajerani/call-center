


def format_phone_number(phone_number):
    # Remove any non-digit characters
    digits = "".join(filter(str.isdigit, phone_number))
    # If the first digit is 1 and there are 11 digits, drop the first digit
    if len(digits) == 11 and digits[0] == "1":
        digits = digits[1:]
    # Ensure we have exactly 10 digits
    if len(digits) != 10:
        raise ValueError("Phone number must contain exactly 10 digits")

    # Format as XXX-XXX-XXXX
    return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
