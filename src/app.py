"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from enum import Enum
from typing import Optional
import os
from pathlib import Path

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


# ============================================================================
# Role-Based Access Control Models and System
# ============================================================================

class UserRole(str, Enum):
    """User roles in the system"""
    ADMIN = "admin"
    STUDENT = "student"


class User(BaseModel):
    """User model"""
    email: str
    role: UserRole
    name: str


class UserRegistration(BaseModel):
    """User registration request"""
    email: str
    name: str


class RoleUpdate(BaseModel):
    """Request to update a user's role"""
    new_role: UserRole


# In-memory user database
users = {
    "admin@mergington.edu": {
        "email": "admin@mergington.edu",
        "name": "Administrator",
        "role": "admin"
    }
}


def get_current_user(authorization: Optional[str] = Header(None)) -> User:
    """Dependency to get the current user from the Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Missing authorization header"
        )

    # Extract email from "Bearer <email>" format
    try:
        scheme, email = authorization.split()
        if scheme.lower() != "bearer":
            raise ValueError("Invalid scheme")
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Use 'Bearer <email>'"
        )

    if email not in users:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    user_data = users[email]
    return User(**user_data)


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    return current_user



activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


# ============================================================================
# User Management Endpoints
# ============================================================================

@app.post("/users/register")
def register_user(user_data: UserRegistration):
    """Register a new user (defaults to student role)"""
    if user_data.email in users:
        raise HTTPException(
            status_code=400,
            detail="User already exists"
        )

    # Create new user with student role by default
    users[user_data.email] = {
        "email": user_data.email,
        "name": user_data.name,
        "role": UserRole.STUDENT
    }

    return {
        "message": f"User {user_data.email} registered successfully",
        "user": users[user_data.email]
    }


@app.get("/users/me")
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user


@app.get("/users")
def list_all_users(current_user: User = Depends(require_admin)):
    """List all users (admin only)"""
    return {
        "total_users": len(users),
        "users": list(users.values())
    }


@app.put("/users/{email}/role")
def update_user_role(
    email: str,
    role_update: RoleUpdate,
    admin_user: User = Depends(require_admin)
):
    """Update a user's role (admin only)"""
    if email not in users:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    # Prevent self-demotion
    if email == admin_user.email and role_update.new_role != UserRole.ADMIN:
        raise HTTPException(
            status_code=400,
            detail="Cannot demote yourself from admin role"
        )

    users[email]["role"] = role_update.new_role
    return {
        "message": f"User {email} role updated to {role_update.new_role}",
        "user": users[email]
    }


# ============================================================================
# Activity Management Endpoints (with role-based restrictions)
# ============================================================================

@app.get("/activities")
def get_activities(current_user: User = Depends(get_current_user)):
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str,
    current_user: User = Depends(get_current_user)
):
    """Sign up a student for an activity (student and admin only)"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str,
    email: str,
    current_user: User = Depends(get_current_user)
):
    """Unregister a student from an activity (student and admin only)"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
