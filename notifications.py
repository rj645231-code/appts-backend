import os,urllib.request,urllib.error,json
RESEND_API_KEY=os.getenv("RESEND_API_KEY","re_H1uG8A3j_LftcqTBL6nD2vDdVv5xDEjuJ")
FROM_EMAIL="onboarding@resend.dev"
ENABLED=bool(RESEND_API_KEY)
def _send(to,sub,html):
    print(f"[NOTIFY] Sending to {to}")
    try:
        p=json.dumps({"from":f"APPTS <{FROM_EMAIL}>","to":[to],"subject":sub,"html":html}).encode()
        r=urllib.request.Request("https://api.resend.com/emails",data=p,headers={"Authorization":f"Bearer {RESEND_API_KEY}","Content-Type":"application/json"},method="POST")
        with urllib.request.urlopen(r,timeout=10) as res:
            print(f"[NOTIFY] SUCCESS: {json.loads(res.read()).get('id')}")
    except Exception as e:
        print(f"[NOTIFY] ERROR: {e}")
def notify_otp(email,name,otp):
    print(f"\n====\n  OTP: {otp}  <-- USE THIS\n====\n")
    _send(email,f"APPTS OTP: {otp}",f"<h2 style='color:#4f8ef7'>{otp}</h2><p>Expires in 10 minutes.</p>")
def notify_task_assigned(e,n,t,p,d=None,desc=None):_send(e,f"[APPTS] Task: {t}",f"<p>Task: {t}<br>Project: {p}</p>")
def notify_task_completed(e,n,eng,t,p):_send(e,f"[APPTS] Done: {t}",f"<p>{eng} completed {t}</p>")
def notify_deadline_warning(e,n,t,p,d):_send(e,f"[APPTS] Deadline: {t}",f"<p>Due: {d}</p>")
def notify_approval_request(e,n,un,ue,r):_send(e,f"[APPTS] Approve: {un}",f"<p>{un} needs approval. Role: {r}</p>")
def notify_user_approved(e,n):_send(e,"[APPTS] Approved",f"<p>Hi {n}, your account is approved!</p>")
def notify_user_rejected(e,n,r=""):_send(e,"[APPTS] Not Approved",f"<p>Hi {n}. {r}</p>")
