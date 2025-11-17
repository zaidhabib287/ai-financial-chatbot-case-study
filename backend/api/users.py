from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.auth.dependencies import get_admin_user, get_current_active_user
from backend.models.database import get_db
from backend.models.models import Transaction, User
from backend.models.schemas import BalanceResponse
from backend.models.schemas import User as UserSchema
from backend.models.schemas import UserUpdate

router = APIRouter()


@router.get("/profile", response_model=UserSchema)
async def get_profile(current_user: User = Depends(get_current_active_user)):
    """Get current user profile"""
    return current_user


@router.put("/profile", response_model=UserSchema)
async def update_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update current user profile"""
    for field, value in user_update.dict(exclude_unset=True).items():
        setattr(current_user, field, value)

    await db.commit()
    await db.refresh(current_user)
    return current_user


@router.get("/balance", response_model=BalanceResponse)
async def get_balance(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get user balance and daily spending information"""
    # Calculate today's spending
    today = func.date(func.now())
    result = await db.execute(
        select(func.sum(Transaction.amount)).filter(
            Transaction.sender_id == current_user.id,
            func.date(Transaction.created_at) == today,
            Transaction.status == "completed",
        )
    )
    daily_spent = result.scalar() or 0.0

    available_today = max(0, current_user.daily_limit - daily_spent)

    return BalanceResponse(
        balance=current_user.balance,
        currency="BHD",
        daily_limit=current_user.daily_limit,
        daily_spent=daily_spent,
        available_today=available_today,
    )


@router.get("/", response_model=List[UserSchema])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """List all users (admin only)"""
    result = await db.execute(select(User).offset(skip).limit(limit))
    users = result.scalars().all()
    return users


@router.get("/{user_id}", response_model=UserSchema)
async def get_user(
    user_id: UUID,
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Get specific user by ID (admin only)"""
    result = await db.execute(select(User).filter(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return user
