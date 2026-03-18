from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import hash_password, verify_password, create_access_token, get_current_user, require_role
from datetime import datetime, timedelta
import random, string, os, json, urllib.request, urllib.error

router = APIRouter(prefix="/users", tags=["Users"])

RESEND_API_KEY = os.getenv("RESEND_API_KEY", "re_H1uG8A3j_LftcqTBL6nD2vDdVv5xDEjuJ")


def _generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


def _send_email(to_email: str, subject: str, html: str) -> bool:
    """Send email via Resend HTTPS API — no SMTP, no port issues."""
    print(f"\n[EMAIL] Attempting to send to: {to_email}")
    print(f"[EMAIL] Subject: {subject}")
    try:
        payload = json.dumps({
            "from": "APPTS <onboarding@resend.dev>",
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
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read())
            print(f"[EMAIL] ✅ SUCCESS! Email ID: {result.get('id')}")
            return True
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        print(f"[EMAIL] ❌ HTTP {e.code}: {body}")
        return False
    except Exception as e:
        print(f"[EMAIL] ❌ FAILED: {type(e).__name__}: {e}")
        return False


def _send_otp_email(to_email: str, name: str, otp: str):
    print(f"\n{'='*60}")
    print(f"  OTP FOR: {to_email}")
    print(f"  CODE:    {otp}  <-- USE THIS")
    print(f"{'='*60}\n")
    html = f"""
    <div style="font-family:Arial;max-width:480px;margin:auto;border:1px solid #ddd;border-radius:10px;overflow:hidden">
      <div style="background:#4f8ef7;padding:20px;color:white">
        <h2 style="margin:0">🔐 Verify Your APPTS Account</h2>
      </div>
      <div style="padding:28px;text-align:center">
        <p>Hi <b>{name}</b>, welcome to APPTS!</p>
        <p style="color:#555">Your verification code is:</p>
        <div style="font-size:48px;font-weight:bold;letter-spacing:16px;color:#4f8ef7;
                    padding:20px;background:#f0f6ff;border-radius:10px;margin:20px 0">
          {otp}
        </div>
        <p style="color:#999;font-size:13px">⏱ Expires in 10 minutes.</p>
      </div>
    </div>"""
    success = _send_email(to_email, f"[APPTS] Your OTP Code: {otp}", html)
    if not success:
        print(f"[EMAIL] Email failed — user must use OTP from admin/logs: {otp}")


# ── REGISTER ─────────────────────────────────────────────
@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    print(f"\n[REGISTER] {user.email}")

    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    is_first_user = db.query(models.User).count() == 0
    otp = _generate_otp()

    new_user = models.User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
        role="admin" if is_first_user else user.role,
        department=user.department,
        is_email_verified=False,
        email_otp=otp,
        otp_expires_at=datetime.utcnow() + timedelta(minutes=10),
        approval_status="approved" if is_first_user else "pending",
        approved_at=datetime.utcnow() if is_first_user else None,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if is_first_user:
        print(f"[REGISTER] First user — auto admin: {new_user.email}")

    _send_otp_email(new_user.email, new_user.name.strip(), otp)
    return {
        "message": "Registration successful. Check your email for OTP.",
        "email": new_user.email,
        "requires_verification": True,
    }


# ── VERIFY OTP ────────────────────────────────────────────
@router.post("/verify-otp")
def verify_otp(body: schemas.VerifyOTPRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_email_verified:
        return {"message": "Email already verified"}
    if not user.email_otp or user.email_otp != body.otp:
        raise HTTPException(status_code=400, detail="Invalid OTP. Check server logs for the code.")
    if user.otp_expires_at and datetime.utcnow() > user.otp_expires_at:
        raise HTTPException(status_code=400, detail="OTP expired. Click Resend OTP.")

    user.is_email_verified = True
    user.email_otp = None
    user.otp_expires_at = None
    db.commit()
    print(f"[VERIFY] ✅ {user.email} verified")
    return {"message": "Email verified! Waiting for admin approval."}


# ── RESEND OTP ────────────────────────────────────────────
@router.post("/resend-otp")
def resend_otp(body: schemas.ResendOTPRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    otp = _generate_otp()
    user.email_otp = otp
    user.otp_expires_at = datetime.utcnow() + timedelta(minutes=10)
    db.commit()

    _send_otp_email(user.email, user.name.strip(), otp)
    return {"message": "New OTP sent.", "otp_for_emailjs": otp, "name": user.name.strip()}


# ── LOGIN ─────────────────────────────────────────────────
@router.post("/login", response_model=schemas.TokenResponse)
def login(credentials: schemas.LoginRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == credentials.email).first()
    if not user or not verify_password(credentials.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_email_verified:
        raise HTTPException(status_code=403, detail="EMAIL_NOT_VERIFIED")
    if user.approval_status == "pending":
        raise HTTPException(status_code=403, detail="APPROVAL_PENDING")
    if user.approval_status == "rejected":
        raise HTTPException(status_code=403, detail="ACCOUNT_REJECTED")

    token = create_access_token({"user_id": user.id, "role": user.role})
    return {"access_token": token, "token_type": "bearer", "user": user}


# ── APPROVE / REJECT ──────────────────────────────────────
@router.patch("/{user_id}/approve")
def approve_user(
    user_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "manager")),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.approval_status == "approved":
        raise HTTPException(status_code=400, detail="Already approved")
    user.approval_status = "approved"
    user.approved_by = current_user.id
    user.approved_at = datetime.utcnow()
    db.commit()

    # notify via resend
    background_tasks.add_task(
        _send_email,
        user.email,
        "[APPTS] Account Approved ✅",
        f"<div style='font-family:Arial;padding:20px'><h2>Account Approved!</h2><p>Hi {user.name.strip()}, you can now log in to APPTS.</p></div>"
    )
    return {"message": f"{user.name.strip()} approved"}


@router.patch("/{user_id}/reject")
def reject_user(
    user_id: int,
    reason: str = "",
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin", "manager")),
):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.approval_status = "rejected"
    user.approved_by = current_user.id
    user.approved_at = datetime.utcnow()
    db.commit()
    return {"message": f"{user.name.strip()} rejected"}


# ── DELETE USER ───────────────────────────────────────────
@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    db.query(models.Task).filter(models.Task.assigned_to == user_id).update({"assigned_to": None})
    db.delete(user)
    db.commit()
    return {"message": f"{user.name.strip()} removed"}


# ── CHANGE ROLE ───────────────────────────────────────────
from pydantic import BaseModel as PydanticBase
class RoleUpdateBody(PydanticBase):
    role: str

@router.patch("/{user_id}/role")
def change_role(
    user_id: int,
    body: RoleUpdateBody,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change your own role")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.role not in ("admin", "manager", "engineer"):
        raise HTTPException(status_code=400, detail="Invalid role")
    user.role = body.role
    db.commit()
    return {"message": f"{user.name.strip()} role changed to {body.role}"}


# ── LIST ──────────────────────────────────────────────────
@router.get("/pending", response_model=list[schemas.UserOut])
def pending_users(db: Session = Depends(get_db), current_user=Depends(require_role("admin", "manager"))):
    return db.query(models.User).filter(models.User.approval_status == "pending").all()

@router.get("/me", response_model=schemas.UserOut)
def get_me(current_user=Depends(get_current_user)):
    return current_user

@router.get("/", response_model=list[schemas.UserOut])
def list_users(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(models.User).all()

@router.get("/engineers", response_model=list[schemas.UserOut])
def list_engineers(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return db.query(models.User).filter(
        models.User.role == "engineer",
        models.User.approval_status == "approved",
    ).all()
