from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
import models, schemas
from auth import create_access_token
from datetime import datetime
import urllib.request
import json
import os

router = APIRouter(prefix="/auth", tags=["Google Auth"])

GOOGLE_CLIENT_ID = os.getenv(
    "GOOGLE_CLIENT_ID",
    "655708632142-85ho1rdfl8b0uv9fmuf0escv3pp8jesi.apps.googleusercontent.com"
)


def verify_google_token(token: str) -> dict:
    """Verify Google ID token and return user info."""
    try:
        url = f"https://oauth2.googleapis.com/tokeninfo?id_token={token}"
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())

        # Verify the token is for our app
        if data.get("aud") != GOOGLE_CLIENT_ID:
            raise HTTPException(status_code=401, detail="Invalid token audience")

        if data.get("email_verified") != "true":
            raise HTTPException(status_code=401, detail="Email not verified by Google")

        return data
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=401, detail="Invalid Google token")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {str(e)}")


from pydantic import BaseModel
class GoogleLoginRequest(BaseModel):
    token: str
    role: str = "engineer"
    department: str = ""
    full_name: str = ""


@router.post("/google")
def google_login(body: GoogleLoginRequest, db: Session = Depends(get_db)):
    """
    Verify Google token, create user if new, return JWT.
    Email is auto-verified since Google guarantees it.
    """
    # Verify token with Google
    google_data = verify_google_token(body.token)

    email = google_data.get("email")
    name = body.full_name.strip() if body.full_name.strip() else google_data.get("name", email.split("@")[0])
    picture = google_data.get("picture", "")

    if not email:
        raise HTTPException(status_code=400, detail="Could not get email from Google")

    # Check if user exists
    user = db.query(models.User).filter(models.User.email == email).first()

    if user:
        # Existing user — check approval
        if user.approval_status == "pending":
            raise HTTPException(status_code=403, detail="APPROVAL_PENDING")
        if user.approval_status == "rejected":
            raise HTTPException(status_code=403, detail="ACCOUNT_REJECTED")

        # Update verification status if needed
        if not user.is_email_verified:
            user.is_email_verified = True
            db.commit()

    else:
        # New user — create account
        is_first_user = db.query(models.User).count() == 0

        user = models.User(
            name=name,
            email=email,
            password="GOOGLE_AUTH",  # no password for Google users
            role="admin" if is_first_user else body.role,
            department=body.department,
            is_email_verified=True,  # Google guarantees email is verified
            approval_status="approved" if is_first_user else "pending",
            approved_at=datetime.utcnow() if is_first_user else None,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        print(f"[GOOGLE AUTH] New user: {email} | First user: {is_first_user}")

        if not is_first_user:
            # Notify admins about new pending user
            admins = db.query(models.User).filter(
                models.User.role.in_(["admin", "manager"]),
                models.User.approval_status == "approved",
            ).all()
            print(f"[GOOGLE AUTH] Notifying {len(admins)} admins about new user")

        if user.approval_status == "pending":
            raise HTTPException(
                status_code=403,
                detail="APPROVAL_PENDING"
            )

    # Generate JWT
    token = create_access_token({"user_id": user.id, "role": user.role})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "department": user.department,
            "created_at": user.created_at.isoformat(),
            "is_email_verified": user.is_email_verified,
            "approval_status": user.approval_status,
        }
    }
