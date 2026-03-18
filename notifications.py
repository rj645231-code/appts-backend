import os
import urllib.request
import urllib.error
import json

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "re_H1uG8A3j_LftcqTBL6nD2vDdVv5xDEjuJ")
FROM_EMAIL = "onboarding@resend.dev"
ENABLED = bool(RESEND_API_KEY)


def _send(to_email, subject, html):
    print(f"[NOTIFY] Sending to {to_email}: {subject}")
    if not ENABLED:
        print("[NOTIFY] RESEND_API_KEY not set")
        return
    try:
        payload = json.dumps({
            "from": f"APPTS <{FROM_EMAIL}>",
            "to": [to_email],
            "subject": subject,
            "html": html,
        }).encode("utf-8")
        req = urllib.request.Request(
            "https://api.resend.com/emails",
            data=payload,
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            print(f"[NOTIFY] SUCCESS ID: {result.get('id')}")
    except urllib.error.HTTPError as e:
        print(f"[NOTIFY] HTTP ERROR {e.code}: {e.read().decode()}")
    except Exception as e:
        print(f"[NOTIFY] ERROR: {type(e).__name__}: {e}")


def notify_otp(email, name, otp):
    print(f"\n{'='*60}\n  OTP: {otp}  <-- USE THIS\n{'='*60}\n")
    html = f"""<div style="font-family:Arial;max-width:480px;margin:auto;border:1px solid #ddd;border-radius:10px;overflow:hidden">
<div style="background:#4f8ef7;padding:20px;color:white"><h2 style="margin:0">Verify Your APPTS Account</h2></div>
<div style="padding:28px;text-align:center">
<p>Hi <b>{name}</b>, welcome to APPTS!</p>
<div style="font-size:44px;font-weight:bold;letter-spacing:12px;color:#4f8ef7;padding:20px;background:#f0f6ff;border-radius:10px;margin:16px 0">{otp}</div>
<p style="color:#999;font-size:13px">Expires in 10 minutes.</p>
</div></div>"""
    _send(email, f"APPTS OTP: {otp}", html)


def notify_task_assigned(engineer_email, engineer_name, task_name, project_name, deadline=None, description=None):
    html = f"""<div style="font-family:Arial;padding:20px"><h2>New Task: {task_name}</h2>
<p>Project: {project_name}</p>{f'<p>Deadline: {deadline}</p>' if deadline else ''}
{f'<p>{description}</p>' if description else ''}</div>"""
    _send(engineer_email, f"[APPTS] New Task: {task_name}", html)


def notify_task_completed(manager_email, manager_name, engineer_name, task_name, project_name):
    html = f"""<div style="font-family:Arial;padding:20px"><h2>Task Completed</h2>
<p>{engineer_name} completed: {task_name}</p><p>Project: {project_name}</p></div>"""
    _send(manager_email, f"[APPTS] Completed: {task_name}", html)


def notify_deadline_warning(engineer_email, engineer_name, task_name, project_name, deadline):
    html = f"""<div style="font-family:Arial;padding:20px"><h2>Deadline Tomorrow</h2>
<p>Task: {task_name}</p><p>Due: {deadline}</p></div>"""
    _send(engineer_email, f"[APPTS] Deadline Tomorrow: {task_name}", html)


def notify_approval_request(admin_email, admin_name, new_user_name, new_user_email, role):
    html = f"""<div style="font-family:Arial;padding:20px"><h2>New User Needs Approval</h2>
<p>Name: {new_user_name}</p><p>Email: {new_user_email}</p><p>Role: {role}</p></div>"""
    _send(admin_email, f"[APPTS] Approve: {new_user_name}", html)


def notify_user_approved(user_email, user_name):
    html = f"""<div style="font-family:Arial;padding:20px"><h2>Account Approved!</h2>
<p>Hi {user_name}, you can now log in to APPTS.</p></div>"""
    _send(user_email, "[APPTS] Account Approved", html)


def notify_user_rejected(user_email, user_name, reason=""):
    html = f"""<div style="font-family:Arial;padding:20px"><h2>Account Not Approved</h2>
<p>Hi {user_name}.</p>{f'<p>Reason: {reason}</p>' if reason else ''}</div>"""
    _send(user_email, "[APPTS] Account Not Approved", html)
