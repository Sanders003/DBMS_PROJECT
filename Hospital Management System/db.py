import mysql.connector as mysql
from datetime import timedelta, datetime


def get_db_connection():
    return mysql.connect(
        host="localhost",
        port="3306",
        user="root",
        password="your_password", # Enter your password of sql server
        database="database_name", # Enter your database name
    )


def get_user_by_username_and_role(username, role):
    db = get_db_connection()
    cursor = db.cursor()
    query = (
        "SELECT id, username, password, role FROM users WHERE username=%s AND role=%s"
    )
    cursor.execute(query, (username, role))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    return user


def get_password_by_user(user_id, username):
    db = get_db_connection()
    cursor = db.cursor()
    query = "SELECT password FROM users WHERE user_id=%s and username = %s"
    values = (user_id, username)
    cursor.execute(query, values)
    password = cursor.fetchone()[0]
    cursor.close()
    db.close()
    return password


def get_user_by_id(user_id):
    db = get_db_connection()
    cursor = db.cursor()
    query = "SELECT id, username, role FROM users WHERE id = %s"
    cursor.execute(query, (user_id,))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    return user


def user_exists(username, role):
    db = get_db_connection()
    cursor = db.cursor()
    query = "SELECT id FROM users WHERE username = %s AND role = %s"
    cursor.execute(query, (username, role))
    exists = cursor.fetchone() is not None
    cursor.close()
    db.close()
    return exists


def add_user(username, password, name, email, role):
    db = get_db_connection()
    cursor = db.cursor()
    query = "INSERT INTO users (username, password, name, email, role) VALUES (%s, %s, %s, %s, %s)"
    cursor.execute(query, (username, password, name, email, role))
    db.commit()
    user_id = cursor.lastrowid
    cursor.close()
    db.close()
    return user_id


def add_doctor(user_id, name, shift, specialization):
    db = get_db_connection()
    cursor = db.cursor()
    query = "INSERT INTO doctors (doctor_id, name, shift, specialization) VALUES (%s, %s, %s, %s)"
    cursor.execute(query, (user_id, name, shift, specialization))
    db.commit()
    cursor.close()
    db.close()


def update_user_password(user_id, new_password):
    db = get_db_connection()
    cursor = db.cursor()
    query = "UPDATE users SET password = %s WHERE id = %s"
    values = (new_password, user_id)
    try:
        cursor.execute(query, values)
        db.commit()
        return True
    except Exception as e:
        print(f"[DB Error] update_user_password: {e}")
        return False
    finally:
        cursor.close()
        db.close()


def display_all_users(page=1, per_page=10):
    offset = (page - 1) * per_page
    db = get_db_connection()
    cursor = db.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    total_pages = (total_users + per_page - 1) // per_page

    query = "SELECT id, username, name, email, role FROM users LIMIT %s OFFSET %s"
    cursor.execute(query, (per_page, offset))
    users = cursor.fetchall()

    cursor.close()
    db.close()
    return users, total_pages


def delete_user(user_id):
    db = get_db_connection()
    cursor = db.cursor()
    query = "DELETE FROM users WHERE id = %s"
    cursor.execute(query, (user_id,))
    db.commit()
    cursor.close()
    db.close()


def display_doctors():
    db = get_db_connection()
    cursor = db.cursor()
    query = "SELECT doctor_id, name, shift, specialization FROM doctors"
    cursor.execute(query)
    doctors = cursor.fetchall()
    cursor.close()
    db.close()
    return doctors


def is_doctor_available(doctor_id, appointment_date, appointment_time):
    db = get_db_connection()
    cursor = db.cursor()
    query = """
        SELECT COUNT(*) FROM appointments
        WHERE doctor_id = %s AND appointment_date = %s AND appointment_time = %s
    """
    values = (doctor_id, appointment_date, appointment_time)
    cursor.execute(query, values)
    count = cursor.fetchone()[0]
    cursor.close()
    db.close()
    return count == 0  # True if no conflict


def register_patient_data(
    name, dob, gender, contact, address, status, today, room_id=None
):
    db = get_db_connection()
    cursor = db.cursor()

    admission_date = today if status == "admitted" else None
    discharge_date = today if status == "discharged" else None

    query = """
        INSERT INTO patients 
        (name, dob, gender, contact, address, status, admission_date, discharge_date, room_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    values = (
        name,
        dob,
        gender,
        contact,
        address,
        status,
        admission_date,
        discharge_date,
        room_id,
    )
    cursor.execute(query, values)
    patient_id = cursor.lastrowid

    if status == "admitted" and room_id:
        cursor.execute(
            "UPDATE rooms SET current_occupancy = current_occupancy + 1 WHERE id = %s",
            (room_id,),
        )

    db.commit()
    query = "SELECT * FROM patients WHERE id = %s"
    cursor.execute(query, (patient_id,))
    patient = cursor.fetchone()
    cursor.close()
    db.close()
    return patient
def edit_patient_data(patient_id, name, dob, gender, contact, address, status, room_id):
    db = get_db_connection()
    cursor = db.cursor()

    # Get the current room_id and status of the patient
    cursor.execute("SELECT room_id, status FROM patients WHERE id = %s", (patient_id,))
    current_room_id, current_status = cursor.fetchone()
    
    status_change = current_status != status
    room_change = current_room_id != room_id

    # If discharged, set room_id to None
    if status == "discharged":
        room_id = None

    # Update patient data
    query = """
        UPDATE patients
        SET name=%s, dob=%s, gender=%s, contact=%s, address=%s, status=%s, room_id=%s
        WHERE id=%s
    """
    values = (name, dob, gender, contact, address, status, room_id, patient_id)
    cursor.execute(query, values)

    # Handle room occupancy updates
    if current_status == "admitted":
        if status == "discharged":
            # Discharging patient: decrease occupancy in current room
            if current_room_id:
                cursor.execute(
                    "UPDATE rooms SET current_occupancy = current_occupancy - 1 WHERE id = %s",
                    (current_room_id,)
                )
        elif status == "admitted" and room_change:
            # Moved to a different room: update both rooms
            if current_room_id:
                cursor.execute(
                    "UPDATE rooms SET current_occupancy = current_occupancy - 1 WHERE id = %s",
                    (current_room_id,)
                )
            if room_id:
                cursor.execute(
                    "UPDATE rooms SET current_occupancy = current_occupancy + 1 WHERE id = %s",
                    (room_id,)
                )
    elif current_status != "admitted" and status == "admitted":
        # Newly admitted patient: increase occupancy in new room
        if room_id:
            cursor.execute(
                "UPDATE rooms SET current_occupancy = current_occupancy + 1 WHERE id = %s",
                (room_id,)
            )

    db.commit()
    cursor.close()
    db.close()



def get_patient_by_id(patient_id):
    db = get_db_connection()
    cursor = db.cursor()
    query = "SELECT id, name, dob, gender, contact, address, status, admission_date, discharge_date, room_id FROM patients WHERE id = %s"
    cursor.execute(query, (patient_id,))
    patient = cursor.fetchone()
    cursor.close()
    db.close()
    return patient


def get_available_rooms():
    db = get_db_connection()
    cursor = db.cursor()
    query = "SELECT id, room_number FROM rooms WHERE current_occupancy < capacity"
    cursor.execute(query)
    rooms = cursor.fetchall()
    cursor.close()
    db.close()
    return rooms


def add_treatment(patient_id, doctor_id, treatment_name, description, treatment_date):
    db = get_db_connection()
    cursor = db.cursor()
    query = "INSERT INTO treatments (patient_id, doctor_id, treatment_name, description, treatment_date) VALUES (%s,%s, %s, %s, %s)"
    values = (patient_id, doctor_id, treatment_name, description, treatment_date)
    cursor.execute(query, values)
    db.commit()
    cursor.close()
    db.close()


def add_prescription(patient_id, doctor_id, prescription, date_prescribed):
    db = get_db_connection()
    cursor = db.cursor()
    query = """
        INSERT INTO prescriptions (patient_id, doctor_id, prescription, date_prescribed)
        VALUES (%s, %s, %s, %s)
    """
    values = (patient_id, doctor_id, prescription, date_prescribed)
    cursor.execute(query, values)
    db.commit()
    cursor.close()
    db.close()


def add_test(patient_id, test_name, result, test_date, pdf_path=None):
    db = get_db_connection()
    cursor = db.cursor()
    query = "INSERT INTO tests (patient_id, test_name, result, test_date, pdf_path) VALUES (%s, %s, %s, %s, %s)"
    values = (patient_id, test_name, result, test_date, pdf_path)
    cursor.execute(query, values)
    db.commit()
    cursor.close()
    db.close()


# Function to fetch all tests associated with the patient
def get_tests_by_id(patient_id):
    db = get_db_connection()
    cursor = db.cursor()
    query = "SELECT * FROM tests WHERE patient_id = %s"
    cursor.execute(query, (patient_id,))
    tests = cursor.fetchall()
    cursor.close()
    db.close()
    return tests


def get_doctor_by_id(doctor_id):
    db = get_db_connection()
    cursor = db.cursor()
    query = """
        SELECT doctor_id, name, shift, specialization
        FROM doctors
        WHERE doctor_id = %s
    """
    cursor.execute(query, (doctor_id,))
    doctor = cursor.fetchone()
    cursor.close()
    db.close()
    return doctor


def get_available_time_slots(doctor_id, appointment_date):
    db = get_db_connection()
    cursor = db.cursor()

    # Get doctor's shift
    query = "SELECT shift FROM doctors WHERE doctor_id = %s"
    values = (doctor_id,)
    cursor.execute(query, values)
    shift = cursor.fetchone()[0]

    query = """
        SELECT appointment_time FROM appointments
        WHERE doctor_id = %s AND appointment_date = %s
    """
    values = (doctor_id, appointment_date)
    cursor.execute(query, values)
    booked_times = [
        (datetime.min + row[0]).strftime("%H:%M") for row in cursor.fetchall()
    ]

    # Define shift time ranges
    shift_times = {"morning": (6, 12), "afternoon": (12, 18), "night": (18, 24)}

    start_hour, end_hour = shift_times.get(
        shift, (6, 12)
    )  # Default to morning if no shift

    available_slots = []
    current_time = datetime.combine(datetime.today(), datetime.min.time()) + timedelta(
        hours=start_hour
    )
    end_time = datetime.combine(datetime.today(), datetime.min.time()) + timedelta(
        hours=end_hour
    )

    while current_time < end_time:
        slot_str = current_time.strftime("%H:%M")
        if slot_str not in booked_times:
            available_slots.append((slot_str, slot_str))
        current_time += timedelta(minutes=30)  # 30-minute intervals

    cursor.close()
    db.close()
    return available_slots


def add_appointment(
    patient_id, doctor_id, appointment_date, appointment_time, reason, priority
):
    db = get_db_connection()
    cursor = db.cursor()

    query = """
        INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time, reason, priority)
        VALUES (%s, %s, %s, %s, %s, %s)
    """
    values = (
        patient_id,
        doctor_id,
        appointment_date,
        appointment_time,
        reason,
        priority,
    )
    cursor.execute(query, values)
    db.commit()
    cursor.close()
    db.close()


def get_appointments_by_doctor(doctor_id, date1=""):
    db = get_db_connection()
    cursor = db.cursor()

    if date1:
        query = """
            SELECT * FROM appointments 
            WHERE doctor_id = %s AND appointment_date = %s 
            ORDER BY appointment_date DESC, appointment_time DESC
        """
        values = (doctor_id, date1)
    else:
        query = """
            SELECT * FROM appointments 
            WHERE doctor_id = %s 
            ORDER BY appointment_date DESC, appointment_time DESC
        """
        values = (doctor_id,)

    cursor.execute(query, values)
    appointments = cursor.fetchall()
    cursor.close()
    db.close()
    return appointments


def display_rooms():
    db = get_db_connection()
    cursor = db.cursor()
    query = "SELECT * FROM rooms"
    cursor.execute(query)
    rooms = cursor.fetchall()
    cursor.close()
    db.close()
    return rooms


def update_password_by_email(email, new_password):
    db = get_db_connection()
    cursor = db.cursor()
    query = "UPDATE users SET password = %s WHERE email = %s"
    values = (new_password, email)
    cursor.execute(query, values)
    db.commit()
    cursor.close()
    db.close()


def user_exists_by_email(email):
    db = get_db_connection()
    cursor = db.cursor()
    query = "SELECT id FROM users WHERE email = %s"
    cursor.execute(query, (email,))
    exists = cursor.fetchone() is not None
    cursor.close()
    db.close()
    return exists


def get_user_by_username(username):
    db = get_db_connection()
    cursor = db.cursor()
    query = "SELECT * FROM users WHERE username = %s"
    cursor.execute(query, (username,))
    user = cursor.fetchone()
    cursor.close()
    db.close()
    return user


def get_password_by_user_id(user_id):
    db = get_db_connection()
    cursor = db.cursor()
    query = "SELECT password FROM users WHERE id=%s"
    cursor.execute(query, (user_id,))
    password = cursor.fetchone()
    cursor.close()
    db.close()
    return password


# import random
# from flask_bcrypt import Bcrypt

# bcrypt = Bcrypt()

# Set up the database connection
# db = get_db_connection()
# cursor = db.cursor()

# # Roles and parameters
# roles = ['front_desk', 'data_entry', 'doctor', 'admin']
# user_count_per_role = 5

# # Define possible shifts and specializations
# shifts = ['Morning','Afternoon', 'Night']
# specializations = ['Cardiology', 'Neurology', 'Orthopedics', 'Dermatology', 'Pediatrics', 'General Medicine']

# for role in roles:
#     user_id=1
#     for i in range(user_count_per_role):
#         username = f"{role.replace('_', '')}{user_id}"
#         name = f"{role.title().replace('_', ' ')} {user_id}"
#         password = f"{role.title().replace('_', ' ')}123"
#         email = f"{username}@gmail.com"

#         # For doctors, assign a random shift and specialization
#         shift = None
#         specialization = None
#         if role == 'doctor':
#             shift = random.choice(shifts)  # Randomly pick a shift
#             specialization = random.choice(specializations)  # Randomly pick a specialization

#         # Hash the password using Bcrypt
#         hash_password = bcrypt.generate_password_hash(password).decode("utf-8")

#         # Insert the user into the users table
#         query = """
#         INSERT INTO users (username, password, name, email, role)
#         VALUES (%s, %s, %s, %s, %s)
#         """
#         values = (username, hash_password, name, email, role)

#         cursor.execute(query, values)

#         # Get the ID of the inserted user (for doctors)
#         user_id_db = cursor.lastrowid  # Get the last inserted user ID
#         db.commit()  # Commit after user insertion
#         print(f"Inserted user: {username} ({role})")

#         # If the role is 'doctor', insert additional information into the doctors table
#         if role == 'doctor':
#             doctor_query = """
#             INSERT INTO doctors (doctor_id, name, shift, specialization)
#             VALUES (%s, %s, %s, %s)
#             """
#             cursor.execute(doctor_query, (user_id_db, name, shift, specialization))
#             db.commit()
#             print(f"Added doctor: {user_id_db} with shift '{shift}' and specialization '{specialization}'")

#         user_id += 1

# cursor.close()
# db.close()


# db=get_db_connection()
# cursor = db.cursor()

# for floor in range(5):  # Floors 0–9
#     for room in range(1, 5):  # Rooms 01–10
#         room_number = f"{floor:01d}{room:02d}"  # e.g., 001, 002 ... 910
#         cursor.execute("INSERT INTO rooms (room_number, capacity) VALUES (%s, %s)", (room_number, 2))

# db.commit()
# cursor.close()
# db.close()
# print("✅ Inserted 100 rooms.")
