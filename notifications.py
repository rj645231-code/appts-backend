"""
Email notification helpers for APPTS.
Uses Python's built-in smtplib — no extra packages needed.

Configure these env variables (or edit defaults below):
  SMTP_HOST     e.g. smtp.gmail.com
  SMTP_PORT     e.g. 587
  SMTP_USER     your Gmail address
  SMTP_PASS     your Gmail App Password (not your login password)
  NOTIFY_FROM   display name in From field
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import os

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.getenv("SMTP_USER", "rvlife9269@gmail.com")
SMTP_PASS = os.getenv("SMTP_PASS", "uyqrrtunozxuwcmk")
NOTIFY_FROM = "APPTS System"
ENABLED = bool(SMTP_USER and SMTP_PASS)


def _send(to_email: str, subject: str, html: str):
    """Send one email. Silently skips if SMTP not configured."""
    if not ENABLED:
        print(f"[NOTIFY] Email disabled. Would send to {to_email}: {subject}")
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{NOTIFY_FROM} <{SMTP_USER}>"
        msg["To"] = to_email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
        print(f"[NOTIFY] Email sent to {to_email}: {subject}")
    except Exception as e:
        print(f"[NOTIFY] Failed to send email to {to_email}: {e}")


def notify_task_assigned(engineer_email: str, engineer_name: str,
                          task_name: str, project_name: str,
                          deadline: str = None, description: str = None):
    deadline_row = f"<p><b>Deadline:</b> {deadline}</p>" if deadline else ""
    desc_row = f"<p><b>Description:</b> {description}</p>" if description else ""
    html = f"""
    <div style="font-family:Arial;max-width:540px;margin:auto;border:1px solid #ddd;border-radius:10px;overflow:hidden">
      <div style="background:#4f8ef7;padding:20px;color:white">
        <h2 style="margin:0">📋 New Task Assigned</h2>
      </div>
      <div style="padding:24px">
        <p>Hi <b>{engineer_name}</b>,</p>
        <p>A new task has been assigned to you in <b>APPTS</b>.</p>
        <table style="background:#f8f9fa;border-radius:8px;padding:16px;width:100%">
          <tr><td><b>Task:</b></td><td>{task_name}</td></tr>
          <tr><td><b>Project:</b></td><td>{project_name}</td></tr>
          {"<tr><td><b>Deadline:</b></td><td>" + deadline + "</td></tr>" if deadline else ""}
        </table>
        {desc_row}
        <p style="color:#666;font-size:13px;margin-top:24px">Log in to APPTS to view and update your task.</p>
      </div>
    </div>
    """
    _send(engineer_email, f"[APPTS] New Task: {task_name}", html)


def notify_deadline_warning(engineer_email: str, engineer_name: str,
                             task_name: str, project_name: str, deadline: str):
    html = f"""
    <div style="font-family:Arial;max-width:540px;margin:auto;border:1px solid #ddd;border-radius:10px;overflow:hidden">
      <div style="background:#f59e0b;padding:20px;color:white">
        <h2 style="margin:0">⚠️ Task Deadline Approaching</h2>
      </div>
      <div style="padding:24px">
        <p>Hi <b>{engineer_name}</b>,</p>
        <p>Your task is due <b>within 24 hours</b>. Please update your progress.</p>
        <table style="background:#fff8e1;border-radius:8px;padding:16px;width:100%">
          <tr><td><b>Task:</b></td><td>{task_name}</td></tr>
          <tr><td><b>Project:</b></td><td>{project_name}</td></tr>
          <tr><td><b>Deadline:</b></td><td style="color:#e53935"><b>{deadline}</b></td></tr>
        </table>
        <p style="color:#666;font-size:13px;margin-top:24px">Log in to APPTS to update your progress immediately.</p>
      </div>
    </div>
    """
    _send(engineer_email, f"[APPTS] ⚠️ Deadline Tomorrow: {task_name}", html)


def notify_task_completed(manager_email: str, manager_name: str,
                           engineer_name: str, task_name: str, project_name: str):
    html = f"""
    <div style="font-family:Arial;max-width:540px;margin:auto;border:1px solid #ddd;border-radius:10px;overflow:hidden">
      <div style="background:#22c55e;padding:20px;color:white">
        <h2 style="margin:0">✅ Task Completed</h2>
      </div>
      <div style="padding:24px">
        <p>Hi <b>{manager_name}</b>,</p>
        <p><b>{engineer_name}</b> has marked a task as <b>completed</b>.</p>
        <table style="background:#f0fdf4;border-radius:8px;padding:16px;width:100%">
          <tr><td><b>Task:</b></td><td>{task_name}</td></tr>
          <tr><td><b>Project:</b></td><td>{project_name}</td></tr>
        </table>
      </div>
    </div>
    """
    _send(manager_email, f"[APPTS] ✅ Task Completed: {task_name}", html)


def notify_otp(email: str, name: str, otp: str):
    html = f"""
    <div style="font-family:Arial;max-width:480px;margin:auto;border:1px solid #ddd;border-radius:10px;overflow:hidden">
      <div style="background:#4f8ef7;padding:20px;color:white">
        <h2 style="margin:0">🔐 Verify Your Email</h2>
      </div>
      <div style="padding:28px;text-align:center">
        <p>Hi <b>{name}</b>, welcome to APPTS!</p>
        <p style="color:#555;margin:10px 0">Use this OTP to verify your email address:</p>
        <div style="font-size:42px;font-weight:700;letter-spacing:12px;color:#4f8ef7;padding:20px;background:#f0f6ff;border-radius:10px;margin:16px 0">{otp}</div>
        <p style="color:#999;font-size:13px">This code expires in <b>10 minutes</b>. Do not share it with anyone.</p>
      </div>
    </div>
    """
    _send(email, f"[APPTS] Your OTP Code: {otp}", html)


def notify_approval_request(admin_email: str, admin_name: str,
                              new_user_name: str, new_user_email: str, role: str):
    html = f"""
    <div style="font-family:Arial;max-width:480px;margin:auto;border:1px solid #ddd;border-radius:10px;overflow:hidden">
      <div style="background:#7c5cfc;padding:20px;color:white">
        <h2 style="margin:0">👤 New User Awaiting Approval</h2>
      </div>
      <div style="padding:24px">
        <p>Hi <b>{admin_name}</b>,</p>
        <p>A new user has registered and is waiting for your approval:</p>
        <table style="background:#f8f4ff;border-radius:8px;padding:16px;width:100%;margin:12px 0">
          <tr><td><b>Name:</b></td><td>{new_user_name}</td></tr>
          <tr><td><b>Email:</b></td><td>{new_user_email}</td></tr>
          <tr><td><b>Role:</b></td><td style="text-transform:capitalize">{role}</td></tr>
        </table>
        <p style="color:#666;font-size:13px">Log in to APPTS as Admin/Manager to approve or reject this user.</p>
      </div>
    </div>
    """
    _send(admin_email, f"[APPTS] New User Approval Required: {new_user_name}", html)


def notify_user_approved(user_email: str, user_name: str):
    html = f"""
    <div style="font-family:Arial;max-width:480px;margin:auto;border:1px solid #ddd;border-radius:10px;overflow:hidden">
      <div style="background:#22c55e;padding:20px;color:white">
        <h2 style="margin:0">✅ Account Approved!</h2>
      </div>
      <div style="padding:24px;text-align:center">
        <p>Hi <b>{user_name}</b>,</p>
        <p style="font-size:15px;margin:12px 0">Your APPTS account has been <b style="color:#22c55e">approved</b>.</p>
        <p>You can now log in and start working on your projects.</p>
      </div>
    </div>
    """
    _send(user_email, "[APPTS] ✅ Your Account Has Been Approved", html)


def notify_user_rejected(user_email: str, user_name: str, reason: str = ""):
    html = f"""
    <div style="font-family:Arial;max-width:480px;margin:auto;border:1px solid #ddd;border-radius:10px;overflow:hidden">
      <div style="background:#ef4444;padding:20px;color:white">
        <h2 style="margin:0">❌ Account Not Approved</h2>
      </div>
      <div style="padding:24px">
        <p>Hi <b>{user_name}</b>,</p>
        <p>Unfortunately your APPTS account registration was not approved.</p>
        {"<p><b>Reason:</b> " + reason + "</p>" if reason else ""}
        <p style="color:#666;font-size:13px">Please contact your manager for more information.</p>
      </div>
    </div>
    """
    _send(user_email, "[APPTS] Account Registration Update", html)
