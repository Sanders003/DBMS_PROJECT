# 🏥 Hospital Management System

A web-based Hospital Management System built using **Flask** and **MySQL**, designed to manage hospital operations through role-specific dashboards including Admin, Doctor, Front Desk, and Data Entry.

## 📂 Project Structure

```

Hospital Management System/
├── app.py                     # Main Flask app
├── db.py                      # Database helper file
├── DBMS hospital Project.session.sql  # SQL script for Database setup
├── static/
│   └── css/                   # CSS files for various dashboards
|        ├── admin_dashboard.html
│        ├── doctor_dashboard.html
│        ├── data_entry_dashboard.html
│        ├── front_desk_dashboard.html
│        └── home.html
├── templates/                # Jinja2 HTML templates
│   ├── admin_dashboard.html
│   ├── doctor_dashboard.html
│   ├── data_entry_dashboard.html
│   ├── front_desk_dashboard.html
│   ├── login.html
│   ├── login.html
│   ├── login.html
│   ├── login.html
│   └── home.html
└── .vscode/                  # VSCode config

````

## 🚀 Features

- 🔐 **Login System**
  - Role-based access: Admin, Doctor, Front Desk, Data Entry
  - Forgot Password: Set a new password after OTP verification
  - Reset Password: Requires old password for validation

- 🧾 **Front Desk Dashboard**
  - Register new patients
  - Schedule appointments for patients on availability of docktors
  - Assign rooms

- 👨‍⚕️ **Doctor Dashboard**
  - View appointments of Doctors
  - Enter treatment details for patients

- 🧪 **Data Entry Dashboard**
  - Record test results
  - Upload PDF test reports

- 🧑‍💼 **Admin Dashboard**
  - Add new users
  - Delete users
  - Displays all users

## 🛠️ Tech Stack

- **Backend**: Python, Flask
- **Database**: MySQL
- **Frontend**: HTML, CSS
- **Authentication**: Flask session
- **File Uploads**: PDF test reports
- **Password Reset**: forgot password and reset password 

## ⚙️ Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/Sanders003/DBMS_PROJECT.git
cd DBMS_PROJECT-main
````

### 2. Set up Virtual Environment (optional)

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up MySQL Database

* Open MySQL and run the SQL script:

```sql
Create a Connection with SQL database and setup database with help of contents of DBMS hospital Project.session.sql
```

* Update `db.py` with your database credentials:

```python
host = "localhost"
user = "your_user"
password = "your_password"
database = "your_database"
```

### 5. Run the Application

```bash
python app.py
```

Visit [http://localhost:5000](http://localhost:5000) in your browser.

## 🛡️ Default Credentials

> Change after first login.

* Admin: `admin` / `admin123`

## 📧 OTP and Email Setup

For forgot password functionality via OTP, set up SMTP details inside `app.py` (if using email).

## 📌 To Do / Improvements

* Add Docker support
* Improve UI responsiveness
* Add testing and logging
* Implement email-based OTP verification
* Add appointment notifications

## 🤝 Contributing

Pull requests are welcome. Please open an issue first to discuss major changes.
- [Hemanth Kumar](https://github.com/Sanders003)
- [Prajwal](https://github.com/Megakyper)
- Ramcharan
- [Vamsi](https://github.com/Raju-Manthena)

## 📄 License

This project is for academic use under the [MIT License](LICENSE).

---

