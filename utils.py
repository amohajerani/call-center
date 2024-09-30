import psycopg2

from dotenv import load_dotenv
import os

# Ensure environment variables are loaded
load_dotenv()

# Get the connection string from environment variables
connection_string = os.getenv("DATABASE_URL")


def connect_to_db():
    # Check if the connection string is not None before creating the database
    if connection_string is not None:
        conn = psycopg2.connect(connection_string)
    else:
        raise ValueError("DATABASE_URL environment variable is not set")
    return conn


def get_member_information(phone_number: str) -> dict:
    """
    This function retrieves all the member's information, including their name, contact information, age, gender, medical conditions, past and future appointments.
    Args:
        phone_number (str): member's phone number, formatted as XXX-XXX-XXXX

    Returns:
        str: information about the member's name, contact information, age, gender, medical conditions, past and future appointments.
    """
    conn = connect_to_db()
    cur = conn.cursor()
    print(f"phone_number in the function call: {phone_number}")
    query = f"""
    SELECT 
        id, first_name, last_name, phone_number, 
        date_of_birth, gender, street_address, city, 
        state, zip_code, email
    FROM members
    WHERE phone_number = '{phone_number}'
    """
    print(f"query: {query}")
    cur.execute(query)
    result = cur.fetchone()

    if not result:
        return {"error": f"Member not found with phone number {phone_number}"}

    member_id = result[0]
    first_name = result[1]
    last_name = result[2]
    date_of_birth = str(result[4])
    gender = result[5]
    street_address = result[6]
    city = result[7]
    state = result[8]
    zip_code = result[9]
    email = result[10]

    # find all the member's appointments
    query = f"""
    SELECT 
        a.id, a.date, a.time, a.street_address, a.city, 
        a.state, a.zip_code,  a.status,
        p.first_name AS provider_first_name, p.last_name AS provider_last_name
    FROM appointments a
    JOIN providers p ON a.provider_id = p.id
    WHERE a.member_phone = '{phone_number}'
    ORDER BY a.date DESC, a.time DESC
    """
    cur.execute(query)
    appointments = cur.fetchall()
    conn.close()

    appointment_descriptions = []
    for appointment in appointments:
        appointment_id = appointment[0]
        appointment_date = appointment[1].strftime("%B %d, %Y")
        appointment_time = appointment[2].strftime("%I:%M %p")
        appointment_status = appointment[7].capitalize()
        provider_name = f"{appointment[8]} {appointment[9]}"

        description = f"Appointment ID {appointment_id}: Appointment on {appointment_date} at {appointment_time} with Dr. {provider_name}. "
        description += f"Location: {appointment[3]}, {appointment[4]}, {appointment[5]} {appointment[6]}. "
        description += f"Status: {appointment_status}."

        appointment_descriptions.append(description)

    # Check if there are no appointments and set the description accordingly
    if len(appointment_descriptions) == 0:
        appointment_descriptions.append("No past or future appointments.")

    member_info = f"""
    Member's information pulled from the database:
    Member ID: {member_id}
    First Name: {first_name}
    Last Name: {last_name}
    Phone Number: {phone_number}
    Date of Birth: {date_of_birth}
    Gender: {gender}
    Address: {street_address}, {city}, {state} {zip_code}
    Email: {email}
    Appointments:
    {chr(10).join(f"- {appointment}" for appointment in appointment_descriptions)}
    """
    return member_info


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
