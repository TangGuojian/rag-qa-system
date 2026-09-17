from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.mysql import get_db
from app.core.dependencies import get_current_user, require_admin
from app.core.auth import hash_password
from app.models.user import User, UserRole, UserStatus
from app.schemas.user import UserCreate, UserUpdate, UserProfileUpdate, UserResponse

router = APIRouter()


@router.get("", response_model=dict)
def list_users(db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    users = db.query(User).all()
    return {
        "data": [
            UserResponse.model_validate(u).model_dump()
            for u in users
        ]
    }


@router.post("", response_model=dict)
def create_user(req: UserCreate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    existing = db.query(User).filter(User.username == req.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="用户名已存在")
    role = UserRole.ADMIN if req.role == "admin" else UserRole.USER
    new_user = User(
        username=req.username,
        password_hash=hash_password(req.password),
        display_name=req.display_name or req.username,
        email=req.email,
        role=role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return UserResponse.model_validate(new_user).model_dump()


@router.get("/me", response_model=dict)
def get_my_profile(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return UserResponse.model_validate(user).model_dump()


def _normalize(value: str | None) -> str | None:
    """空字符串统一存成 NULL，语义是「沿用系统默认配置」。"""
    if value is None:
        return None
    value = value.strip()
    return value or None


def _normalize_base(value: str | None) -> str | None:
    """顺手去掉地址结尾多余的斜杠——手工粘贴时很常见。"""
    value = _normalize(value)
    return value.rstrip("/") if value else None


@router.put("/me", response_model=dict)
def update_my_profile(req: UserProfileUpdate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    if req.display_name is not None:
        user.display_name = req.display_name
    # 只有请求里显式带了这些字段才更新，避免「只改显示名」时把已存的 Key 清掉
    if "api_key" in req.model_fields_set:
        user.api_key = _normalize(req.api_key)
    if "api_base" in req.model_fields_set:
        user.api_base = _normalize_base(req.api_base)
    if "llm_model" in req.model_fields_set:
        user.llm_model = _normalize(req.llm_model)
    if "embedding_model" in req.model_fields_set:
        user.embedding_model = _normalize(req.embedding_model)
    db.commit()
    db.refresh(user)
    return UserResponse.model_validate(user).model_dump()


@router.put("/{user_id}", response_model=dict)
def update_user(user_id: int, req: UserUpdate, db: Session = Depends(get_db), current_user: User = Depends(require_admin)):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    if req.display_name is not None:
        u.display_name = req.display_name
    if req.email is not None:
        u.email = req.email
    if req.role is not None:
        u.role = UserRole.ADMIN if req.role == "admin" else UserRole.USER
    if req.status is not None:
        u.status = UserStatus.ACTIVE if req.status == "active" else UserStatus.DISABLED
    db.commit()
    db.refresh(u)
    return UserResponse.model_validate(u).model_dump()
