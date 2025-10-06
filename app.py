import streamlit as st
import qrcode
import sqlite3
import os
from datetime import datetime
from PIL import Image
from geopy.distance import geodesic
from streamlit_geolocation import streamlit_geolocation

# ---------- CONFIG ----------

OFFICE_LAT, OFFICE_LON = 17.443387, 78.348673
# Example: Hyderabad
MAX_DISTANCE_KM = 8.0                          # 5 km for easier demo testing
DB_FILE = "attendance.db"

# ---------- DATABASE ----------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS employees
                 (emp_id TEXT PRIMARY KEY,
                  name TEXT,
                  department TEXT,
                  role TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS attendance
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  emp_id TEXT,
                  name TEXT,
                  date TEXT,
                  login_time TEXT,
                  logout_time TEXT,
                  hours_worked REAL,
                  FOREIGN KEY(emp_id) REFERENCES employees(emp_id))''')

    c.execute("SELECT COUNT(*) FROM employees")
    if c.fetchone()[0] == 0:
        employees = [
            ("101", "Alice Johnson", "HR", "HR Manager"),
            ("102", "Bob Smith", "IT", "Software Engineer"),
            ("103", "Carol Lee", "Finance", "Accountant"),
            ("104", "David Brown", "Sales", "Sales Executive"),
            ("105", "Emma Davis", "IT", "DevOps Engineer"),
            ("106", "Frank Wilson", "Finance", "Financial Analyst"),
            ("107", "Grace Miller", "HR", "Recruiter"),
            ("108", "Henry Clark", "IT", "Backend Engineer"),
            ("109", "Irene Lewis", "Sales", "Sales Associate"),
            ("110", "Jack Hall", "IT", "Frontend Engineer"),
            ("111", "Kate Young", "HR", "HR Associate"),
            ("112", "Liam Walker", "IT", "QA Engineer"),
            ("113", "Mia Allen", "Finance", "Auditor"),
            ("114", "Noah Scott", "Sales", "Sales Manager"),
            ("115", "Olivia King", "IT", "Data Scientist"),
        ]
        c.executemany("INSERT INTO employees VALUES (?, ?, ?, ?)", employees)

    conn.commit()
    conn.close()


def validate_employee(emp_id, name):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM employees WHERE emp_id=? AND name=?", (emp_id, name))
    result = c.fetchone()
    conn.close()
    return result


def get_record(emp_id, date):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT * FROM attendance WHERE emp_id=? AND date=?", (emp_id, date))
    record = c.fetchone()
    conn.close()
    return record


def mark_login(emp_id, name, date):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    login_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO attendance (emp_id, name, date, login_time) VALUES (?, ?, ?, ?)",
              (emp_id, name, date, login_time))
    conn.commit()
    conn.close()
    return login_time


def mark_logout(emp_id, date):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    logout_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    c.execute("SELECT login_time FROM attendance WHERE emp_id=? AND date=?", (emp_id, date))
    login_time = c.fetchone()[0]
    login_dt = datetime.strptime(login_time, "%Y-%m-%d %H:%M:%S")
    logout_dt = datetime.strptime(logout_time, "%Y-%m-%d %H:%M:%S")
    hours = round((logout_dt - login_dt).total_seconds() / 3600, 2)

    c.execute("UPDATE attendance SET logout_time=?, hours_worked=? WHERE emp_id=? AND date=?",
              (logout_time, hours, emp_id, date))
    conn.commit()
    conn.close()
    return logout_time, hours


def get_today_attendance():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    today = datetime.now().strftime("%Y-%m-%d")
    c.execute("SELECT emp_id, name, login_time, logout_time, hours_worked FROM attendance WHERE date=?", (today,))
    records = c.fetchall()
    conn.close()
    return records


# ---------- GEOLOCATION ----------
def get_user_location():
    """Capture user's current location safely via streamlit-geolocation"""
    st.write("📍 Click the button below to share your current location.")
    location = streamlit_geolocation()

    # Avoid KeyErrors when data is empty
    if location and isinstance(location, dict) and "latitude" in location and "longitude" in location:
        lat, lon = location["latitude"], location["longitude"]
        st.success(f"✅ Location captured: ({lat:.5f}, {lon:.5f})")
        return lat, lon
    else:
        st.info("Please click the location button above and allow permission.")
        return None


def within_office(lat, lon, radius_km=MAX_DISTANCE_KM):
    dist = geodesic((lat, lon), (OFFICE_LAT, OFFICE_LON)).km
    return dist <= radius_km, round(dist, 3)


# ---------- STREAMLIT APP ----------
st.set_page_config(page_title="QR Attendance System", page_icon="📌")
st.title("📌 QR Attendance System with Location Validation")

init_db()

# ----- SINGLE STATIC QR -----
QR_FOLDER = "qrcodes"
os.makedirs(QR_FOLDER, exist_ok=True)
qr_file_path = os.path.join(QR_FOLDER, "company_qr.png")

if not os.path.exists(qr_file_path):
    base_url = "https://qrforhr.streamlit.app/"  # your Streamlit Cloud URL
    qr = qrcode.make(base_url)
    qr.save(qr_file_path)

# ----- MAIN APP -----
role = st.radio("Login as:", ["Employee", "HR/Admin"])

if role == "Employee":
    st.subheader("Employee Attendance Portal")
    st.image(qr_file_path, caption="Scan this QR to open attendance app", width=250)
    st.info("📱 You can also open this app link directly from your mobile.")

    emp_id = st.text_input("Enter Employee ID")
    name = st.text_input("Enter Name")

    if emp_id.strip() and name.strip():
        employee = validate_employee(emp_id, name)
        if not employee:
            st.error("❌ Employee not found. Please check your ID and Name.")
        else:
            location = get_user_location()
            if location:
                lat, lon = location
                is_inside, dist = within_office(lat, lon)
                if not is_inside:
                    st.error(f"❌ You are {dist*1000:.1f} meters away from office. Attendance not allowed.")
                else:
                    st.success("✅ You are inside the office premises!")
                    today = datetime.now().strftime("%Y-%m-%d")
                    record = get_record(emp_id, today)
                    if not record:
                        login_time = mark_login(emp_id, name, today)
                        st.success(f"🕒 Login recorded at {login_time}")
                    elif record[5] is None:
                        logout_time, hours = mark_logout(emp_id, today)
                        st.success(f"🕒 Logout recorded at {logout_time}. Hours worked: {hours}")
                    else:
                        st.warning("⚠️ You already logged out today.")
            else:
                st.info("Please share your location to mark attendance.")

elif role == "HR/Admin":
    st.subheader("HR Dashboard")
    password = st.text_input("Enter HR Password", type="password")
    if password == "admin123":
        st.success("Welcome HR!")
        records = get_today_attendance()
        if records:
            st.table([{
                "ID": r[0], "Name": r[1], "Login": r[2],
                "Logout": r[3] if r[3] else "-",
                "Hours": r[4] if r[4] else "-"
            } for r in records])
        else:
            st.info("No attendance records for today.")
    elif password:
        st.error("Invalid HR password")
