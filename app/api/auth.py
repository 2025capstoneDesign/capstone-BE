from fastapi import APIRouter

router = APIRouter()

@router.get("/login")
async def user_login():
    return {"message": "User Log In"}


@router.get("/logout")
async def user_logout():
    return {"message": "User Log Out"}