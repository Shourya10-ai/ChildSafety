import asyncio
import os
import sys
import uuid
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select
from app.models.user import User
from app.models.moderator import Moderator
from app.core.security import get_password_hash, create_access_token
from run_local_dev import dev_sessionmaker

async def seed():
    async with dev_sessionmaker() as db:
        # 1. Check or create moderator
        res = await db.execute(select(User).where(User.email == "moderator@safety.gov.in"))
        mod_user = res.scalar_one_or_none()
        if not mod_user:
            mod_user = User(
                email="moderator@safety.gov.in",
                hashed_password=get_password_hash("Moderator@123"),
                role="moderator",
                full_name="Safety Duty Officer",
                is_active=True
            )
            db.add(mod_user)
            await db.commit()
            await db.refresh(mod_user)

        mod_res = await db.execute(select(Moderator).where(Moderator.user_id == mod_user.id))
        mod = mod_res.scalar_one_or_none()
        if not mod:
            mod = Moderator(user_id=mod_user.id, is_available=True, active_case_count=0, max_cases=15)
            db.add(mod)
            await db.commit()

        # 2. Check or create admin
        res = await db.execute(select(User).where(User.email == "admin@safety.gov.in"))
        admin_user = res.scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                email="admin@safety.gov.in",
                hashed_password=get_password_hash("Admin@123"),
                role="admin",
                full_name="System Administrator",
                is_active=True
            )
            db.add(admin_user)
            await db.commit()
            await db.refresh(admin_user)

        mod_token = create_access_token(data={"sub": str(mod_user.id), "role": "moderator"})
        admin_token = create_access_token(data={"sub": str(admin_user.id), "role": "admin"})

        print("\n" + "=" * 60)
        print("SEED ACCOUNTS FOR WEB PORTAL INTEGRATION READY")
        print("=" * 60)
        print("Moderator Login:")
        print("  Email:    moderator@safety.gov.in")
        print("  Password: Moderator@123")
        print("  Role:     moderator")
        print(f"  Bearer Token: {mod_token}\n")
        print("Admin Login:")
        print("  Email:    admin@safety.gov.in")
        print("  Password: Admin@123")
        print("  Role:     admin")
        print(f"  Bearer Token: {admin_token}")
        print("=" * 60 + "\n")

if __name__ == "__main__":
    asyncio.run(seed())
