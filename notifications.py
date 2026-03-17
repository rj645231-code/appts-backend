import smtplib, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
NOTIFY_FROM = "APPTS System"
ENABLED = True

def _send(to_email, subject, html):
    print(f"[NOTIFY] Sending to {to_email}")
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{NOTIFY_FROM} <{SMTP_USER}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        print(f"[NOTIFY] SUCCESS sent to {to_email}")
    except Exception as e:
        print(f"[NOTIFY] FAILED: {type(e).__name__}: {e}")

def notify_otp(email, name, otp):
    print(f"\n{'='*60}\n  OTP:  {otp}  <-- USE THIS CODE\n{'='*60}\n")
    html = f"<div style='font-family:Arial;padding:20px'><h2>Your APPTS OTP</h2><div style='font-size:40px;font-weight:bold;color:#4f8ef7;letter-spacing:10px'>{otp}</div><p>Expires in 10 minutes.</p></div>"
    _send(email, f"[APPTS] Your OTP Code: {otp}", html)

def notify_task_assigned(engineer_email, engineer_name, task_name, project_name, deadline=None, description=None):
    html = f"<div style='font-family:Arial;padding:20px'><h2>New Task: {task_name}</h2><p>Project: {project_name}</p></div>"
    _send(engineer_email, f"[APPTS] New Task: {task_name}", html)

def notify_task_completed(manager_email, manager_name, engineer_name, task_name, project_name):
    html = f"<div style='font-family:Arial;padding:20px'><h2>Task Completed: {task_name}</h2><p>By: {engineer_name}</p></div>"
    _send(manager_email, f"[APPTS] Task Completed: {task_name}", html)

def notify_deadline_warning(engineer_email, engineer_name, task_name, project_name, deadline):
    html = f"<div style='font-family:Arial;padding:20px'><h2>Deadline Tomorrow: {task_name}</h2><p>Due: {deadline}</p></div>"
    _send(engineer_email, f"[APPTS] Deadline Tomorrow: {task_name}", html)

def notify_approval_request(admin_email, admin_name, new_user_name, new_user_email, role):
    html = f"<div style='font-family:Arial;padding:20px'><h2>New User: {new_user_name}</h2><p>Email: {new_user_email} | Role: {role}</p></div>"
    _send(admin_email, f"[APPTS] Approve User: {new_user_name}", html)

def notify_user_approved(user_email, user_name):
    html = f"<div style='font-family:Arial;padding:20px'><h2>Account Approved!</h2><p>Hi {user_name}, you can now log in.</p></div>"
    _send(user_email, "[APPTS] Account Approved", html)

def notify_user_rejected(user_email, user_name, reason=""):
    html = f"<div style='font-family:Arial;padding:20px'><h2>Account Not Approved</h2><p>Hi {user_name}. {reason}</p></div>"
    _send(user_email, "[APPTS] Account Not Approved", html)
