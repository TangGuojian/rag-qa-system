from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.mysql import get_db
from app.core.auth import hash_password, verify_password, create_access_token
from app.core.config import settings
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import LoginRequest, TokenResponse

router = APIRouter()


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="账号已被禁用")
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    token = create_access_token({"sub": str(user.id), "role": user.role.value})
    return TokenResponse(token=token, role=user.role.value, expires_in=settings.jwt_expire_hours * 3600)


@router.post("/init")
def init_admin(db: Session = Depends(get_db)):
    admin = db.query(User).filter(User.role == UserRole.ADMIN).first()
    if admin:
        return {"message": "管理员已存在"}
    admin = User(
        username="admin",
        password_hash=hash_password("admin123"),
        display_name="系统管理员",
        role=UserRole.ADMIN,
    )
    db.add(admin)
    db.commit()
    return {"message": "管理员创建成功", "username": "admin", "password": "admin123"}
