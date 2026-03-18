import os
import urllib.request
import urllib.error
import json

RESEND_API_KEY = os.getenv('RESEND_API_KEY', 're_H1uG8A3j_LftcqTBL6nD2vDdVv5xDEjuJ')
FROM_EMAIL = 'onboarding@resend.dev'
ENABLED = bool(RESEND_API_KEY)

def _send(to_email, subject, html):
    print(f'[NOTIFY] Sending to {to_email}')
    try:
        payload = json.dumps({'from': f'APPTS <{FROM_EMAIL}>', 'to': [to_email], 'subject': subject, 'html': html}).encode('utf-8')
        req = urllib.request.Request('https://api.resend.com/emails', data=payload, headers={'Authorization': f'Bearer {RESEND_API_KEY}', 'Content-Type': 'application/json'}, method='POST')
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            print(f'[NOTIFY] SUCCESS ID: {result.get(id)}')
    except Exception as e:
        print(f'[NOTIFY] ERROR: {type(e).__name__}: {e}')

def notify_otp(email, name, otp):
    print(f'OTP: {otp}')
    html = f'<h2>Your APPTS OTP: {otp}</h2><p>Expires in 10 minutes.</p>'
    _send(email, f'APPTS OTP: {otp}', html)

def notify_task_assigned(e, n, t, p, d=None, desc=None): _send(e, f'[APPTS] Task: {t}', f'<p>Task {t} assigned. Project: {p}</p>')
def notify_task_completed(e, n, eng, t, p): _send(e, f'[APPTS] Completed: {t}', f'<p>{eng} completed {t}</p>')
def notify_deadline_warning(e, n, t, p, d): _send(e, f'[APPTS] Deadline: {t}', f'<p>Due: {d}</p>')
def notify_approval_request(e, n, un, ue, r): _send(e, f'[APPTS] Approve: {un}', f'<p>{un} needs approval</p>')
def notify_user_approved(e, n): _send(e, '[APPTS] Approved', f'<p>Hi {n}, account approved!</p>')
def notify_user_rejected(e, n, r=''): _send(e, '[APPTS] Not Approved', f'<p>Hi {n}. {r}</p>')
