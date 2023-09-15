from flask import Flask, render_template, request, redirect, url_for, session
from azure.storage.blob import BlobServiceClient
import time
import threading
from datetime import datetime

app = Flask(__name__)
app.secret_key = "06092544"

# Azure Blob Storage configuration
connection_string = 'DefaultEndpointsProtocol=https;AccountName=nook1212;AccountKey=uhqpVxTTXzVw6AwU2EIjSEswFbQWOsytg/4LfBRtjRJNQG5DmQ/xt5BbUXPOgK7akuOQfEkLwTle+ASt9bfwGA==;EndpointSuffix=core.windows.net'
container_name = 'data'
blob_name = 'input1'

blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

current_blob_content = []
update_time = None

# User data for login
users = {
    "admin": "password123",
    "jack": "123456",
    "panadda": "63201198"
}

def update_blob_content():
    global current_blob_content
    global update_time
    while True:
        blob_data = container_client.get_blob_client(blob_name).download_blob()
        updated_blob_content = blob_data.readall().decode('utf-8').splitlines()

        if updated_blob_content != current_blob_content:
            current_blob_content = updated_blob_content[-19:]  # เก็บเฉพาะ 10 บรรทัดสุดท้าย
            update_time = datetime.now()

        time.sleep(1)  # รอ 1 นาที (60 วินาที) ก่อนที่จะอัปเดตอีกครั้ง

@app.before_request
def check_login():
    if "username" not in session and request.endpoint != "login":
        return redirect(url_for("login"))

@app.route("/")
def index():
    if "username" in session:
        return redirect(url_for("show_current_content"))
    else:
        return redirect(url_for("login"))  # เปลี่ยนเส้นทางไปที่หน้า Login

@app.route('/login', methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        if username in users and users[username] == password:
            session["username"] = username
            session["logged_in"] = True
            return redirect(url_for("show_current_content"))  # เมื่อล็อกอินสำเร็จ ให้เปลี่ยนเส้นทางไปที่หน้าแสดงข้อมูลหลัก
        else:
            return "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง"

    return render_template("login.html")

@app.route('/logout')
def logout():
    session.pop("username", None)
    session.pop("logged_in", None)
    return redirect(url_for("login"))

@app.route('/dashboard')
def show_current_content():
    if "logged_in" in session and session["logged_in"]:
        current_time = datetime.now()

        if current_blob_content:
            last_nineteen_lines = "\n".join(current_blob_content[-19:])
        else:
            last_nineteen_lines = "No data available."

        if (current_time - update_time).total_seconds() <= 10:
            return render_template('dashboard.html', blob_content=last_nineteen_lines)
        else:
            return "OFF"
    else:
        return redirect(url_for("login"))

@app.route('/get_latest_content')
def get_latest_content():
    return "\n".join(current_blob_content)


if __name__ == '__main__':
    update_thread = threading.Thread(target=update_blob_content)
    update_thread.start()
    app.run(debug=True)