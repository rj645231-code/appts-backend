from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import hash_password, verify_password, create_access_token, get_current_user, require_role
from datetime import datetime, timedelta
import random, string, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

router = APIRouter(prefix="/users", tags=["Users"])

SMTP_USER = "rvlife9269@gmail.com"
SMTP_PASS = "uyqrrtunozxuwcmk"

def _generate_otp() -> str:
    return "".join(random.choices(string.digits, k=6))


def _send_otp_email(to_email: str, name: str, otp: str):
    """Send OTP email directly — all errors printed to terminal."""
    print(f"\n{'='*60}")
    print(f"  SENDING OTP EMAIL")
    print(f"  TO:   {to_email}")
    print(f"  NAME: {name}")
    print(f"  OTP:  {otp}  <-- USE THIS CODE")
    print(f"{'='*60}\n")
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"[APPTS] Your OTP Code: {otp}"
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        html = f"""
        <div style="font-family:Arial;max-width:480px;margin:auto;border:1px solid #ddd;border-radius:10px;overflow:hidden">
          <div style="background:#4f8ef7;padding:20px;color:white"><h2 style="margin:0">🔐 Verify Your Email — APPTS</h2></div>
          <div style="padding:28px;text-align:center">
            <p>Hi <b>{name}</b>, welcome to APPTS!</p>
            <p>Your verification code is:</p>
            <div style="font-size:44px;font-weight:700;letter-spacing:14px;color:#4f8ef7;padding:20px;background:#f0f6ff;border-radius:10px;margin:16px 0">{otp}</div>
            <p style="color:#999;font-size:13px">Expires in 10 minutes.</p>
          </div>
        </div>"""
        msg.attach(MIMEText(html, "html"))

        print(f"  Connecting to smtp.gmail.com:587 ...")
        server = smtplib.SMTP("smtp.gmail.com", 587, timeout=15)
        server.ehlo()
        server.starttls()
        server.ehlo()
        print(f"  Logging in as {SMTP_USER} ...")
        server.login(SMTP_USER, SMTP_PASS)
        print(f"  Sending message ...")
        server.sendmail(SMTP_USER, to_email, msg.as_string())
        server.quit()
        print(f"  ✅ OTP EMAIL SENT SUCCESSFULLY to {to_email}")
    except smtplib.SMTPAuthenticationError as e:
        print(f"  ❌ AUTH ERROR: {e}")
        print(f"  Fix: regenerate App Password at myaccount.google.com/apppasswords")
    except Exception as e:
        print(f"  ❌ EMAIL ERROR: {type(e).__name__}: {e}")
        print(f"  --> USE THE OTP ABOVE FROM THE TERMINAL INSTEAD")


# ── REGISTER ─────────────────────────────────────────────
@router.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    print(f"\n[REGISTER] New registration attempt: {user.email}")

    existing = db.query(models.User).filter(models.User.email == user.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # First user ever = auto admin, auto approved, no approval needed
    is_first_user = db.query(models.User).count() == 0

    otp = _generate_otp()
    otp_expires = datetime.utcnow() + timedelta(minutes=10)

    new_user = models.User(
        name=user.name,
        email=user.email,
        password=hash_password(user.password),
        role="admin" if is_first_user else user.role,
        department=user.department,
        is_email_verified=False,
        email_otp=otp,
        otp_expires_at=otp_expires,
        approval_status="approved" if is_first_user else "pending",
        approved_at=datetime.utcnow() if is_first_user else None,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    if is_first_user:
        print(f"[REGISTER] 🌟 FIRST USER — auto-approved as Admin: {new_user.email}")

    print(f"[REGISTER] User saved to DB. Sending OTP now...")
    _send_otp_email(new_user.email, new_user.name.strip(), otp)

    # Notify admins/managers about new pending user
    if not is_first_user:
        approvers = db.query(models.User).filter(
            models.User.role.in_(["admin", "manager"]),
            models.User.approval_status == "approved",
        ).all()
        print(f"[REGISTER] Notifying {len(approvers)} approvers...")

    msg = "Registration successful! You are the first user and have been set as Admin. Verify your email to continue." if is_first_user else "Registration successful. Check your email for OTP. If email fails, use the code printed in the server terminal."

    return {
        "message": msg,
        "email": new_user.email,
        "requires_verification": True,
        "is_first_user": is_first_user,
    }


# ── VERIFY OTP ────────────────────────────────────────────
@router.post("/verify-otp")
def verify_otp(body: schemas.VerifyOTPRequest, db: Session = Depends(get_db)):
    print(f"\n[VERIFY OTP] Email: {body.email}, OTP entered: {body.otp}")
    user = db.query(models.User).filter(models.User.email == body.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.is_email_verified:
        return {"message": "Email already verified"}

    print(f"[VERIFY OTP] Stored OTP: {user.email_otp}, Expires: {user.otp_expires_at}")

    if not user.email_otp or user.email_otp != body.otp:
        raise HTTPException(status_code=400, detail=f"Invalid OTP. Check the server terminal for the correct code.")
    if user.otp_expires_at and datetime.utcnow() > user.otp_expires_at:
        raise HTTPException(status_code=400, detail="OTP expired. Click Resend OTP.")

    user.is_email_verified = True
    user.email_otp = None
    user.otp_expires_at = None
    db.commit()
    print(f"[VERIFY OTP] ✅ Email verified for {user.email}")
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
    return {"message": "New OTP sent. Check email or server terminal."}


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
    print(f"[APPROVE] {user.name} approved by {current_user.name}")
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
    print(f"[REJECT] {user.name} rejected by {current_user.name}")
    return {"message": f"{user.name.strip()} rejected"}


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


# ── DELETE USER (admin only) ──────────────────────────────
@router.delete("/{user_id}")
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(require_role("admin")),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot delete yourself")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    # Unassign their tasks first
    db.query(models.Task).filter(models.Task.assigned_to == user_id).update({"assigned_to": None})
    db.delete(user)
    db.commit()
    print(f"[DELETE USER] {user.name} deleted by {current_user.name}")
    return {"message": f"{user.name.strip()} has been removed"}


# ── CHANGE ROLE (admin only) ──────────────────────────────
class RoleUpdate(schemas.BaseModel):
    role: str

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
        raise HTTPException(status_code=400, detail="You cannot change your own role")
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.role not in ("admin", "manager", "engineer"):
        raise HTTPException(status_code=400, detail="Invalid role")
    old_role = user.role
    user.role = body.role
    db.commit()
    print(f"[ROLE CHANGE] {user.name}: {old_role} → {body.role} by {current_user.name}")
    return {"message": f"{user.name.strip()} role changed to {body.role}"}