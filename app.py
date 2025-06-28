from flask import (
    Flask,
    render_template,
    redirect,
    request,
    url_for,
    flash,
    jsonify,
    session,
)
from flask_login import (
    UserMixin,
    login_user,
    LoginManager,
    current_user,
    login_required,
    logout_user,
)
from flask_bcrypt import Bcrypt
from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed
from wtforms import (
    StringField,
    PasswordField,
    SubmitField,
    SelectField,
    DateField,
    FileField,
    TextAreaField,
    HiddenField,
)
from wtforms.validators import InputRequired, Length, Regexp, DataRequired
import db  # import your db helper file
from validate_email_address import validate_email
import traceback
import os
from werkzeug.utils import secure_filename
from datetime import date, timedelta, datetime
from flask_mail import Mail, Message
import random


today = date.today().isoformat()
max_date = date.today() + timedelta(days=30)

app = Flask(__name__, static_folder="static")
app.secret_key = "supersecretkey"
bcrypt = Bcrypt(app)

# ---- Flask-Login setup ----
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


# --- for PDF uploads ---
app.config["UPLOAD_FOLDER"] = "static/uploads"
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

# --- For emails ---
app.config.update(
    MAIL_DEFAULT_SENDER="your_email@gmail.com",  # Enter sender email
    MAIL_SERVER="smtp.gmail.com",
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USERNAME="your_email@gmail.com",  # Enter sender email
    MAIL_PASSWORD="password",  # Enter 16 digit code from App Passwords(google settings)
)
mail = Mail(app)


# ---- Login Form ----
class LoginForm(FlaskForm):
    form_name = HiddenField(default="login_form")
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField(validators=[InputRequired(), Length(min=6, max=20)])
    role = SelectField(
        "Role",
        choices=[
            ("front_desk", "Front Desk"),
            ("data_entry", "Data Entry"),
            ("doctor", "Doctor"),
            ("admin", "Admin"),
        ],
        validators=[InputRequired()],
    )
    submit = SubmitField("Login")


# ---- Registration Form for Users ----
class RegisterForm(FlaskForm):
    form_name = HiddenField(default="register_form")
    name = StringField(validators=[InputRequired(), Length(min=4, max=20)])
    email = StringField(validators=[InputRequired(), Length(min=10, max=40)])
    username = StringField(validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField(validators=[InputRequired(), Length(min=6, max=20)])
    role = SelectField(
        "Role",
        choices=[
            ("front_desk", "Front Desk"),
            ("data_entry", "Data Entry"),
            ("doctor", "Doctor"),
            ("admin", "Admin"),
        ],
        validators=[InputRequired()],
    )
    submit = SubmitField("Register")


# ---- Registration Form for Patients ----
class RegisterPatientForm(FlaskForm):
    form_name = HiddenField(default="register_patient_form")
    name = StringField("Name", validators=[InputRequired()])
    dob = DateField("Date of Birth", format="%Y-%m-%d", validators=[InputRequired()])
    gender = SelectField(
        "Gender", choices=[("male", "Male"), ("female", "Female"), ("other", "Other")]
    )
    status = SelectField(
        "Status",
        choices=[
            ("outpatient", "Outpatient"),
            ("admitted", "Admitted"),
            ("discharged", "Discharged"),
        ],
    )
    contact = StringField(
        "Contact",
        validators=[
            DataRequired(),
            Regexp(r"^\d{10}$", message="Enter a 10-digit number"),
        ],
        render_kw={
            "placeholder": "Enter 10-digit number",
            "title": "Enter a 10-digit number",
        },
    )
    address = StringField("Address", validators=[InputRequired()])
    room_id = SelectField("Room ID", choices=[], coerce=int, default=-1)
    submit = SubmitField("Register Patient")


# ---- Edit Form for Patients ----
class EditPatientForm(FlaskForm):
    form_name = HiddenField(default="edit_patient_form")
    name = StringField("Name", validators=[InputRequired()])
    dob = DateField("Date of Birth", format="%Y-%m-%d", validators=[InputRequired()])
    gender = SelectField(
        "Gender", choices=[("male", "Male"), ("female", "Female"), ("other", "Other")]
    )
    status = SelectField(
        "Status",
        choices=[
            ("outpatient", "Outpatient"),
            ("admitted", "Admitted"),
            ("discharged", "Discharged"),
        ],
    )
    contact = StringField(
        "Contact",
        validators=[
            DataRequired(),
            Regexp(r"^\d{10}$", message="Enter a 10-digit number"),
        ],
        render_kw={
            "placeholder": "Enter 10-digit number",
            "title": "Enter a 10-digit number",
        },
    )
    address = StringField("Address", validators=[InputRequired()])
    room_id = SelectField("Room ID", choices=[], coerce=int)
    submit = SubmitField("Edit")


# --- Test Form ---
class TestEntryForm(FlaskForm):
    form_name = HiddenField(default="test_form")
    patient_id = StringField("Patient ID", validators=[InputRequired()])
    test_name = StringField("Test Name", validators=[InputRequired()])
    result = StringField("Result", validators=[InputRequired()])
    test_date = DateField("Test Date", format="%Y-%m-%d", validators=[InputRequired()])
    pdf = FileField("Attach PDF", validators=[FileAllowed(["pdf"], "PDFs only!")])
    submit = SubmitField("Record Test")


# --- Prescription Form ---
class PrescriptionEntryForm(FlaskForm):
    form_name = HiddenField(default="prescription_form")
    prescription = StringField("Prescription", validators=[InputRequired()])
    prescription_date = DateField(
        "Date", format="%Y-%m-%d", validators=[InputRequired()]
    )
    submit = SubmitField("Record Prescription")


# --- Treatment Form ---
class TreatmentEntryForm(FlaskForm):
    form_name = HiddenField(default="treatment_form")
    patient_id = StringField("Patient ID", validators=[InputRequired()])
    doctor_id = SelectField("Doctor", coerce=int, validators=[InputRequired()])
    treatment_name = StringField("Treatment", validators=[InputRequired()])
    description = StringField("Description", validators=[InputRequired()])
    treatment_date = DateField("Date", format="%Y-%m-%d", validators=[InputRequired()])
    submit = SubmitField("Record Treatment")


# --- Appointment Form ---
class AppointmentForm(FlaskForm):
    form_name = HiddenField(default="appointment_form")
    patient_id = StringField("Patient ID", validators=[InputRequired()])
    doctor_id = SelectField("Doctor", coerce=int, validators=[InputRequired()])
    appointment_date = DateField(
        "Date", format="%Y-%m-%d", validators=[InputRequired()]
    )
    appointment_time = SelectField("Time", choices=[], validators=[InputRequired()])
    reason = TextAreaField("Reason", validators=[InputRequired()])
    priority = SelectField(
        "Priority",
        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
        default="low",
        validators=[InputRequired()],
    )
    submit = SubmitField("Book Appointment")


# --- Web user ---
class User(UserMixin):
    def __init__(self, id, username, role):
        self.id = id
        self.username = username
        self.role = role


@login_manager.user_loader
def load_user(user_id):
    user_data = db.get_user_by_id(user_id)
    if user_data:
        return User(*user_data)
    return None


@app.route("/")
def index():
    return redirect(url_for("home"))


# Home Page
@app.route("/home")
def home():
    return render_template("home.html")


# Login Page
@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()

    # --- Login ---
    if (
        request.method == "POST"
        and request.form.get("form_name") == "login_form"
        and form.validate()
    ):
        username = form.username.data
        password = form.password.data
        role = form.role.data

        user_data = db.get_user_by_username_and_role(username, role)

        if not user_data:
            flash("Invalid role or username", "login_error")
        elif not bcrypt.check_password_hash(user_data[2], password):
            flash("Wrong password", "login_error")
        else:
            user = User(user_data[0], user_data[1], user_data[3])
            login_user(user)
            flash("User logged in successfully", f"{role}_success")
            return redirect(url_for(f"{role}_dashboard"))

    return render_template("login.html", form=form)


# Admin Dashboard
@app.route("/admin_dashboard", methods=["GET", "POST"])
@login_required
def admin_dashboard():
    if current_user.role != "admin":
        return redirect(url_for("login"))

    form = RegisterForm()

    if (
        request.method == "POST"
        and request.form.get("form_name") == "register_form"
        and form.validate()
    ):
        role = form.role.data
        name = form.name.data
        email = form.email.data
        username = form.username.data
        password = form.password.data

        if not validate_email(email):
            flash("Email doesn't exist.", "admin_error")
        elif db.user_exists(username, role):
            flash(
                f"User '{username}' with role '{role}' already exists.", "admin_error"
            )
        elif db.user_exists_by_email(email):
            flash(f"A User with email '{email}' already exists.", "admin_error")
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode("utf-8")
            user_id = db.add_user(username, hashed_password, name, email, role)
            if isinstance(user_id, str) and user_id.startswith("Error"):
                flash(f"MySQL error: {user_id}", "admin_error")
            else:
                flash("User added successfully!", "admin_success")
                if role == "doctor":
                    shift = request.form.get("shift")
                    specialization = request.form.get("specialization")
                    db.add_doctor(user_id, name, shift, specialization)

    # Handle delete
    delete_id = request.args.get("delete_id")
    if delete_id:
        db.delete_user(delete_id)
        flash("User deleted successfully!", "admin_success")
        return redirect(url_for("admin_dashboard"))

    # Get page number from query parameter
    page = request.args.get("page", 1, type=int)
    users, total_pages = db.display_all_users(page=page, per_page=10)

    return render_template(
        "admin_dashboard.html",
        form=form,
        users=users,
        page=page,
        total_pages=total_pages,
    )


# Logout Route
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("User have been logged out successfully!", "login_info")
    return redirect(url_for("login"))


# Front Desk Dashboard
@app.route("/front_desk_dashboard", methods=["GET", "POST"])
@login_required
def front_desk_dashboard():
    if current_user.role != "front_desk":
        return redirect(url_for("login"))

    register_form = RegisterPatientForm()
    appointment_form = AppointmentForm()
    new_patient_id = None
    patient_id = None

    register_form.room_id.choices = [(-1, "N/A (Not Admitted)")] + [
        (room[0], f"{room[1]} ({room[2]-room[3]})") for room in db.display_rooms()
    ]
    # --- Register New Patients ---
    if (
        request.method == "POST"
        and request.form.get("form_name") == "register_patient_form"
        and register_form.validate()
    ):
        name = register_form.name.data
        dob = register_form.dob.data
        gender = register_form.gender.data
        status = register_form.status.data
        contact = register_form.contact.data
        address = register_form.address.data
        room_id = register_form.room_id.data if status == "admitted" else None
        if status == "admitted" and not room_id:
            flash("Room ID is required for admitted patients.", "register_error")

        try:
            patient_row = db.register_patient_data(
                name, dob, gender, contact, address, status, today, room_id
            )
            if patient_row:
                new_patient_id = patient_row[0]
                flash(
                    "Patient registered and admitted successfully!", "register_success"
                )
                return render_template(
                    "front_desk_dashboard.html",
                    register_form=register_form,
                    appointment_form=appointment_form,
                    patient_id=patient_id,
                    new_patient_id=new_patient_id,
                    today=today,
                )
            else:
                flash("Patient registration failed.", "register_error")
        except Exception as e:
            print("Exception:", traceback.format_exc())

    # --- Appointments ---
    appointment_form.doctor_id.choices = [
        (doc[0], f"{doc[1]} ({doc[3]})") for doc in db.display_doctors()
    ]

    # Update available time slots based on the selected doctor and date
    if appointment_form.doctor_id.data and appointment_form.appointment_date.data:
        doctor_id = appointment_form.doctor_id.data
        appointment_date = appointment_form.appointment_date.data
        available_slots = db.get_available_time_slots(doctor_id, appointment_date)

        if available_slots:
            appointment_form.appointment_time.choices = available_slots
        else:
            appointment_form.appointment_time.choices = []
            flash(
                "No available time slots for the selected doctor on this date.",
                "appointment_error",
            )

    # Appointment booking logic
    if (
        request.method == "POST"
        and request.form.get("form_name") == "appointment_form"
        and appointment_form.validate()
    ):
        patient_id = appointment_form.patient_id.data
        doctor_id = appointment_form.doctor_id.data
        appointment_date = appointment_form.appointment_date.data
        appointment_time = appointment_form.appointment_time.data
        reason = appointment_form.reason.data
        priority = appointment_form.priority.data

        try:
            # Check if the doctor is available for the selected time slot
            if not db.is_doctor_available(
                doctor_id, appointment_date, appointment_time
            ):
                flash(
                    "Doctor is not available at the selected time.", "appointment_error"
                )
            else:
                # Insert appointment into the database
                db.add_appointment(
                    patient_id,
                    doctor_id,
                    appointment_date,
                    appointment_time,
                    reason,
                    priority,
                )
                flash("Appointment booked successfully!", "appointment_success")
                return redirect(url_for("front_desk_dashboard") + "#appointment")

        except Exception:
            print("Exception:", traceback.format_exc())
        return redirect(url_for("front_desk_dashboard"))

    doctors = db.display_doctors()
    return render_template(
        "front_desk_dashboard.html",
        register_form=register_form,
        appointment_form=appointment_form,
        doctors=doctors,
        patient_id=patient_id,
        new_patient_id=None,
        today=today,
    )


# Data Entry Dashboard
@app.route("/data_entry_dashboard", methods=["GET", "POST"])
@login_required
def data_entry_dashboard():
    if current_user.role != "data_entry":
        return redirect(url_for("login"))
    test_form = TestEntryForm()
    treatment_form = TreatmentEntryForm()

    if (
        request.method == "POST"
        and request.form.get("form_name") == "test_form"
        and test_form.submit.data
    ):
        if test_form.validate():
            try:
                patient_id = test_form.patient_id.data
                test_name = test_form.test_name.data
                result = test_form.result.data
                test_date = test_form.test_date.data
                file = test_form.pdf.data
                filename = None
                relative_path = None

                if file and file.filename != "":
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
                    file.save(file_path)
                    relative_path = filename

                db.add_test(patient_id, test_name, result, test_date, relative_path)
                flash("Test recorded successfully!", "test_success")
                return redirect(url_for("data_entry_dashboard") + "#test")

            except Exception:
                print("Exception:", traceback.format_exc())

    treatment_form.doctor_id.choices = [
        (doc[0], f"{doc[1]} ({doc[3]})") for doc in db.display_doctors()
    ]

    if (
        request.method == "POST"
        and request.form.get("form_name") == "treatment_form"
        and treatment_form.submit.data
    ):
        if treatment_form.validate():
            try:
                db.add_treatment(
                    treatment_form.patient_id.data,
                    treatment_form.doctor_id.data,
                    treatment_form.treatment_name.data,
                    treatment_form.description.data,
                    treatment_form.treatment_date.data,
                )
                flash("Treatment recorded successfully!", "treatment_success")
                return redirect(url_for("data_entry_dashboard") + "#treatment")
            except Exception:
                print("Exception:", traceback.format_exc())
        else:
            # Print form validation errors for debugging
            print(treatment_form.errors)

    return render_template(
        "data_entry_dashboard.html",
        test_form=test_form,
        treatment_form=treatment_form,
        today=today,
    )


# Doctor Dashboard
@app.route("/doctor_dashboard", methods=["GET", "POST"])
@login_required
def doctor_dashboard():
    if current_user.role != "doctor":
        return redirect(url_for("login"))

    patient_id = ""

    if request.method == "POST":
        patient_id = request.form.get("patient_id")

        if patient_id:
            try:
                return redirect(url_for("patient_details", patient_id=patient_id))
            except Exception as e:
                flash(f"Error: {str(e)}", "doctor_error")

    doctor_id = current_user.id
    date_str = request.args.get("date")
    if not date_str:
        date_str = date.today().isoformat()

    appointments = db.get_appointments_by_doctor(doctor_id, date_str)

    return render_template(
        "doctor_dashboard.html",
        appointments=appointments,
        patient_id=patient_id,
        today=today,
        max_date=max_date.isoformat(),
        doctor_id=doctor_id,
    )


@app.route("/patient/<int:patient_id>", methods=["GET", "POST"])
@login_required
def patient_details(patient_id):
    if current_user.role != "doctor":
        return redirect(url_for("login"))

    # Fetch patient details and tests
    patient = db.get_patient_by_id(patient_id)
    tests = db.get_tests_by_id(patient_id)

    if patient:
        patient_info = {
            "patient_id": patient[0],
            "name": patient[1],
            "dob": patient[2],
            "gender": patient[3],
            "status": patient[6],
            "room_id": patient[9] if patient[6] == "admitted" else -1,
            "admitted_date": patient[7] if patient[6] == "admitted" else "N/A",
            "discharge_date": patient[8] if patient[6] == "discharge" else "N/A",
        }
    else:
        patient_info = None

    # Handle prescription form submission
    prescription_form = PrescriptionEntryForm()
    if (
        request.method == "POST"
        and request.form.get("form_name") == "prescription_form"
        and prescription_form.validate()
    ):
        doctor_id = current_user.id
        prescription = prescription_form.prescription.data
        date_prescribed = prescription_form.prescription_date.data
        flash("Prescription added successfully!", "prescription_success")
        # Save the prescription to the database
        db.add_prescription(
            patient_id,
            doctor_id,
            prescription,
            date_prescribed,
        )

    return render_template(
        "patient_details.html",
        patient_id=patient_id,
        patient_info=patient_info,
        tests=tests,
        prescription_form=prescription_form,
    )


@app.route("/doctor/<int:doctor_id>/appointments")
@login_required
def view_appointments(doctor_id):
    if current_user.role != "doctor":
        return redirect(url_for("login"))

    all_appointments = db.get_appointments_by_doctor(doctor_id)
    return render_template(
        "appointments.html", appointments=all_appointments, doctor_id=doctor_id
    )


@app.route("/get_time_slots")
def get_time_slots():
    doctor_id = request.args.get("doctor_id", type=int)
    appointment_date = request.args.get("date")

    if not doctor_id or not appointment_date:
        return jsonify([])

    slots = db.get_available_time_slots(doctor_id, appointment_date)
    return jsonify(slots)


@app.route("/edit_patient", methods=["GET", "POST"])
@login_required
def edit_patient():
    if current_user.role != "front_desk":
        return redirect(url_for("login"))

    edit_form = EditPatientForm()
    patient_id = request.args.get("patient_id")
    patient_info = None

    if patient_id:
        patient_info = db.get_patient_by_id(patient_id)

    edit_form.room_id.choices = [
        (room[0], f"{room[1]} ({room[2]-room[3]})") for room in db.display_rooms()
    ]
    if patient_info:
        if (
            request.method == "POST"
            and request.form.get("form_name") == "edit_patient_form"
            and edit_form.validate()
        ):
            try:
                name = edit_form.name.data
                dob = edit_form.dob.data
                gender = edit_form.gender.data
                contact = edit_form.contact.data
                address = edit_form.address.data
                status = edit_form.status.data
                room_id = edit_form.room_id.data if status == "admitted" else None

                db.edit_patient_data(
                    patient_id,
                    name,
                    dob,
                    gender,
                    contact,
                    address,
                    status,
                    room_id,
                )
                flash("Patient edited successfully!", "edit_success")
                return redirect(url_for("edit_patient"))

            except Exception as e:
                flash(f"Error updating patient: {str(e)}", "edit_error")
        else:
            if request.method == "GET":
                # Fill in the form with the existing patient data
                edit_form.name.data = patient_info[1]
                edit_form.dob.data = patient_info[2]
                edit_form.gender.data = patient_info[3]
                edit_form.contact.data = patient_info[4]
                edit_form.address.data = patient_info[5]
                edit_form.status.data = patient_info[6]
                edit_form.room_id.data = (
                    patient_info[9] if patient_info[6] == "admitted" else None
                )

    else:
        flash("No patient found with this ID.", "edit_error")

    return render_template(
        "edit_patient.html",
        edit_form=edit_form,
        patient_id=patient_id,
        today=today,
        patient_info=patient_info,
    )


@app.route("/reset_password", methods=["GET", "POST"])
@login_required
def reset_password():
    if request.method == "POST":
        old_password = request.form.get("old_password")
        new_password = request.form.get("new_password")

        if not old_password or not new_password:
            flash("All fields are required.", "reset_error")
            return redirect(url_for("reset_password"))

        if len(new_password) < 6:
            flash("New password must be at least 6 characters long.", "reset_error")
            return redirect(url_for("reset_password"))

        user_data = db.get_user_by_id(current_user.id)
        password = db.get_password_by_user_id(user_data[0])
        if not user_data or not bcrypt.check_password_hash(password[0], old_password):
            flash("Old password is incorrect.", "reset_error")
            return redirect(url_for("reset_password"))

        hashed_new = bcrypt.generate_password_hash(new_password).decode("utf-8")
        db.update_user_password(current_user.id, hashed_new)
        flash("Password updated successfully!", f"{current_user.role}_success")
        return redirect(url_for(f"{current_user.role}_dashboard"))

    return render_template("reset_password.html")


@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form["username"]
        user = db.get_user_by_username(username)

        # can add rate limit or captcha
        if user:
            email = user[4]
            otp = str(random.randint(100000, 999999))
            session["reset_email"] = email
            session["otp"] = otp
            session["otp_time"] = datetime.now().isoformat()

            msg = Message("OTP for Password Reset", recipients=[email])
            msg.body = f"Your OTP is: {otp}\n\nThis OTP is valid for 10 minutes."
            mail.send(msg)

            flash("OTP sent to your registered email!", "otp_success")
            return redirect(url_for("verify_otp"))
        else:
            flash("Username not found!", "forgot_error")

    return render_template("forgot_password.html")


@app.route("/verify_otp", methods=["GET", "POST"])
def verify_otp():
    if (
        "otp" not in session
        or "otp_time" not in session
        or "reset_email" not in session
    ):
        flash(
            "Session expired or unauthorized access. Please start again.",
            "forgot_error",
        )
        return redirect(url_for("forgot_password"))

    # Check if OTP is expired
    otp_time = datetime.fromisoformat(session["otp_time"])
    if datetime.now() > otp_time + timedelta(minutes=10):
        session.pop("otp", None)
        session.pop("otp_time", None)
        session.pop("reset_email", None)

        flash("OTP expired. Please request a new one.", "forgot_error")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        user_otp = request.form["otp"]
        if user_otp == session.get("otp"):
            return redirect(url_for("set_new_password"))
        else:
            flash("Invalid OTP. Please try again.", "otp_error")

    return render_template("verify_otp.html")


@app.route("/set_new_password", methods=["GET", "POST"])
def set_new_password():
    if "reset_email" not in session:
        flash("Unauthorized access.", "forgot_error")
        return redirect(url_for("forgot_password"))

    if request.method == "POST":
        new_password = request.form["new_password"]

        if not new_password or len(new_password) < 6:
            flash("Password must be at least 6 characters long.", "set_new_error")
            return redirect(url_for("set_new_password"))

        hashed = bcrypt.generate_password_hash(new_password).decode("utf-8")
        db.update_password_by_email(session.get("reset_email"), hashed)

        # Clear all OTP-related session data
        session.pop("reset_email", None)
        session.pop("otp", None)
        session.pop("otp_time", None)

        flash("Password updated successfully!", "login_success")
        return redirect(url_for("login"))

    return render_template("set_new_password.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
