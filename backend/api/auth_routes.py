import os
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status, Form
from supabase import create_client, Client
from pydantic import BaseModel, EmailStr
import jwt
from datetime import datetime, timedelta
from typing import Optional
import json

from nodes import MedicalReportNode
from managers.model_manager import model_manager


# --- Configuration & Setup ---
router = APIRouter(prefix="/auth", tags=["Authentication"])

# Supabase Client
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_API_KEY")
supabase: Client = create_client(url, key)

# JWT Secret for cookies
JWT_SECRET = os.getenv("JWT_SECRET")

# --- Pydantic Models ---
class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str
    age: str
    gender: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    name: str
    email: EmailStr
    age: str
    gender: str
    
medical_report_node = None

def get_medical_report_node():
    """Get or create medical report node with loaded adapter"""
    global medical_report_node
    if medical_report_node is None:
        adapter = model_manager.get_local_adapter()
        if adapter is None:
            raise HTTPException(status_code=503, detail="Models not loaded yet")
        medical_report_node = MedicalReportNode(adapter, supabase)
    return medical_report_node

# --- Helper to set auth cookie ---
def set_auth_cookie(response: Response, user_data: dict):
    """Set auth cookie with user data embedded"""
    to_encode = {
        "sub": str(user_data["id"]),
        "email": user_data["email"],
        "name": user_data.get("name", ""),
        "age": user_data.get("age", ""),
        "gender": user_data.get("gender", ""),
        "exp": datetime.utcnow() + timedelta(days=7)
    }
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm="HS256")
    response.set_cookie(
        key="access_token",
        value=encoded_jwt,
        httponly=True,
        samesite="lax",
        secure=False # Set to True in production with HTTPS
    )

# --- API Endpoints ---
@router.post("/patient/register")
async def register_user(user_data: UserCreate, response: Response):
    try:
        # Create user in Supabase Auth
        user_session = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password,
            "options": {
                "data": {
                    "name": user_data.name,
                    "age": user_data.age,
                    "gender": user_data.gender
                }
            }
        })
        
        if user_session.user:
            try:
                profile_data = {
                    "id": user_session.user.id,
                    "name": user_data.name,
                    "age": user_data.age,
                    "gender": user_data.gender
                }
                
                # Insert or update user profile
                supabase.table("user_profiles").upsert(profile_data).execute()
                print(f"✅ User profile created for {user_session.user.email}")
                
            except Exception as profile_error:
                print(f"⚠️ Failed to create user profile: {profile_error}")
                # Don't fail registration if profile creation fails
            
            # Prepare user data for cookie
            user_cookie_data = {
                "id": user_session.user.id,
                "email": user_session.user.email,
                "name": user_data.name,
                "age": user_data.age,
                "gender": user_data.gender
            }
            
            # Set cookie regardless of email confirmation status
            set_auth_cookie(response, user_cookie_data)
            
            if not user_session.session:
                # Email confirmation required
                return {
                    "message": "Registration successful. Please check your email to confirm your account.",
                    "email_confirmation_required": True,
                    "user": user_cookie_data
                }
            else:
                # No email confirmation required
                return {
                    "message": "Registration successful",
                    "email_confirmation_required": False,
                    "user": user_cookie_data
                }
        else:
            raise HTTPException(status_code=400, detail="Could not register user")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/patient/login")
async def login_user(user_data: UserLogin, response: Response):
    try:
        user_session = supabase.auth.sign_in_with_password({
            "email": user_data.email,
            "password": user_data.password
        })
        if not user_session.user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        try:
            profile_result = supabase.table("user_profiles")\
                .select("*")\
                .eq("id", user_session.user.id)\
                .execute()
            
            if profile_result.data:
                # Use data from user_profiles table
                profile = profile_result.data[0]
                user_cookie_data = {
                    "id": user_session.user.id,
                    "email": user_session.user.email,
                    "name": profile.get("name", ""),
                    "age": profile.get("age", ""),
                    "gender": profile.get("gender", "")
                }
            else:
                # Fallback to user metadata if no profile exists
                user_cookie_data = {
                    "id": user_session.user.id,
                    "email": user_session.user.email,
                    "name": user_session.user.user_metadata.get("name", ""),
                    "age": user_session.user.user_metadata.get("age", ""),
                    "gender": user_session.user.user_metadata.get("gender", "")
                }
                
                # Create missing profile
                try:
                    profile_data = {
                        "id": user_session.user.id,
                        "name": user_cookie_data["name"],
                        "age": user_cookie_data["age"],
                        "gender": user_cookie_data["gender"]
                    }
                    supabase.table("user_profiles").upsert(profile_data).execute()
                    print(f"✅ Created missing user profile for {user_session.user.email}")
                except Exception as e:
                    print(f"⚠️ Failed to create missing profile: {e}")
                    
        except Exception as e:
            print(f"⚠️ Failed to fetch user profile: {e}")
            # Fallback to user metadata
            user_cookie_data = {
                "id": user_session.user.id,
                "email": user_session.user.email,
                "name": user_session.user.user_metadata.get("name", ""),
                "age": user_session.user.user_metadata.get("age", ""),
                "gender": user_session.user.user_metadata.get("gender", "")
            }
        
        set_auth_cookie(response, user_cookie_data)
        
        return {
            "message": "Login successful", 
            "user": user_cookie_data
        }
    except Exception as e:
        print(f"Login error: {e}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/patient/logout")
def logout_user(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Logout successful"}

# --- Dependency to get current user from cookie ---
def get_current_user(request: Request):  #Removed async
    """Get user data directly from JWT cookie instead of calling Supabase"""
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user_id = payload.get("sub")
        if not user_id:
            return None
            
        # Return user data directly from JWT payload
        return {
            "id": user_id,
            "email": payload.get("email", ""),
            "name": payload.get("name", ""),
            "age": payload.get("age", ""),
            "gender": payload.get("gender", "")
        }
    except (jwt.PyJWTError, Exception) as e:
        print(f"JWT decode error: {e}")
        return None

@router.get("/patient/profile")
async def get_session(request: Request):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    #Get fresh data from database
    try:
        profile_result = supabase.table("user_profiles")\
            .select("*")\
            .eq("id", user["id"])\
            .execute()
        
        if profile_result.data:
            profile = profile_result.data[0]
            return {
                "id": user["id"],
                "email": user["email"],  # Email comes from auth, not profile
                "name": profile.get("name", ""),
                "age": profile.get("age", ""),
                "gender": profile.get("gender", "")
            }
        else:
            # Return cookie data if no profile exists
            return user
            
    except Exception as e:
        print(f"⚠️ Failed to fetch profile from database: {e}")
        # Fallback to cookie data
        return user

@router.put("/patient/update_profile")
async def update_profile(profile_data: UserUpdate, request: Request, response: Response):
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        #Update user profile in database
        updated_profile_data = {
            "id": user["id"],
            "name": profile_data.name,
            "age": profile_data.age,
            "gender": profile_data.gender
        }
        
        # Update in database
        result = supabase.table("user_profiles")\
            .upsert(updated_profile_data)\
            .execute()
        
        if not result.data:
            raise Exception("Failed to update profile in database")
        
        #Update the cookie with new data including email
        updated_user_data = {
            "id": user["id"],
            "email": profile_data.email,  # Email might be updated
            "name": profile_data.name,
            "age": profile_data.age,
            "gender": profile_data.gender
        }
        
        # Update auth email if changed
        if profile_data.email != user["email"]:
            try:
                # Note: Updating email in Supabase Auth requires the user to be authenticated
                # Sso this is a simplified version. If in production, need proper email verification
                print(f"⚠️ Email update requested but not implemented: {user['email']} -> {profile_data.email}")
                # For now, keep the original email
                updated_user_data["email"] = user["email"]
            except Exception as email_error:
                print(f"⚠️ Failed to update email: {email_error}")
                updated_user_data["email"] = user["email"]
        
        # Update the cookie
        set_auth_cookie(response, updated_user_data)
        
        print(f"✅ Profile updated successfully for user {user['id']}")
        return updated_user_data
        
    except Exception as e:
        print(f"Profile update error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update profile: {str(e)}")
    
@router.get("/patient/medical-reports")
async def get_user_medical_reports(
    request: Request,
    limit: int = 10,
    offset: int = 0
):
    """Get user's medical reports"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        node = get_medical_report_node()
        reports = await node.get_user_medical_reports(
            user["id"], limit, offset
        )
        return {
            "reports": reports,
            "total": len(reports),
            "limit": limit,
            "offset": offset
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/patient/medical-reports/{report_id}")
async def get_medical_report(
    report_id: str,
    request: Request
):
    """Get a specific medical report"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        node = get_medical_report_node()
        report = await node.get_medical_report_by_id(
            report_id, user["id"]
        )
        if not report:
            raise HTTPException(status_code=404, detail="Medical report not found")
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/patient/save-medical-report")
async def save_medical_report(
    session_id: str = Form(...),
    agent_state: str = Form(...),
    report_title: str | None = Form(None),
    request: Request = None
):
    """Save a medical report to user's account"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        # Parse agent state
        agent_state_dict = json.loads(agent_state)
        
        # Save report using the integrated node
        node = get_medical_report_node()
        saved_report = await node.save_medical_report_to_database(
            user["id"],
            session_id,
            agent_state_dict,
            report_title
        )
        
        return {
            "message": "Medical report saved successfully",
            "report_id": saved_report["id"],
            "report": saved_report
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/patient/medical-reports/{report_id}")
async def delete_medical_report(
    report_id: str,
    request: Request
):
    """Delete a medical report"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        node = get_medical_report_node()
        success = await node.delete_medical_report(
            report_id, user["id"]
        )
        if not success:
            raise HTTPException(status_code=404, detail="Medical report not found")
        return {"message": "Medical report deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.put("/patient/medical-reports/{report_id}/title")
async def update_report_title(
    report_id: str,
    new_title: str = Form(...),
    request: Request = None
):
    """Update medical report title"""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    
    try:
        node = get_medical_report_node()
        updated_report = await node.update_report_title(
            report_id, user["id"], new_title
        )
        if not updated_report:
            raise HTTPException(status_code=404, detail="Medical report not found")
        return updated_report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))