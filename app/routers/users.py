
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.dependencies import get_token_header

router = APIRouter(
    prefix="/users",
    tags=["users"],
    dependencies=[Depends(get_token_header)],
    responses={404: {"description": "Not found"}},
)

class User(BaseModel):
    username: str
    email: str

fake_users_db = {
    "alice": User(username="alice", email="alice@example.com"),
    "bob": User(username="bob", email="bob@example.com")
}

@router.get("/", response_model=list[User])
def list_users():
    """List all users."""
    return list(fake_users_db.values())

@router.get("/{username}", response_model=User)
def get_user(username: str):
    """Get a user by username."""
    user = fake_users_db.get(username)
    if not user:
        return {"error": "User not found"}
    return user

@router.post("/", response_model=User)
def create_user(user: User):
    """Create a new user."""
    if not user.username or user.username in fake_users_db:
        return {"error": "Invalid or duplicate username"}
    fake_users_db[user.username] = user
    return user