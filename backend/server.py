from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.security import HTTPBearer
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import hashlib
import httpx
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from enum import Enum

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# User roles enum
class UserRole(str, Enum):
    STUDENT = "student"
    ISSUER = "issuer"
    VERIFIER = "verifier"

class RequestStatus(str, Enum):
    PENDING = "pending"
    VALIDATED = "validated"
    RECEIVED = "received"
    REJECTED = "rejected"

# Pydantic Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    name: str
    picture: Optional[str] = None
    role: UserRole
    university: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: str
    name: str
    picture: Optional[str] = None
    role: UserRole
    university: Optional[str] = None

class TranscriptRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_request_uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    student_id: str
    student_name: str
    student_email: str
    university_from: str  # Issuer university
    university_to: str    # Verifier university
    document_type: str = "transcript"
    content_hash: str     # SHA-256 hash for integrity
    status: RequestStatus = RequestStatus.PENDING
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    
class TranscriptRequestCreate(BaseModel):
    university_from: str
    university_to: str
    document_type: str = "transcript"
    content: str  # Document content to hash

class IssuerValidation(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    issuer_validation_uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transcript_request_id: str
    issuer_id: str
    issuer_name: str
    validation_notes: Optional[str] = None
    is_approved: bool
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class IssuerValidationCreate(BaseModel):
    transcript_request_id: str
    validation_notes: Optional[str] = None
    is_approved: bool

class VerifierReceipt(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    verifier_receipt_uuid: str = Field(default_factory=lambda: str(uuid.uuid4()))
    transcript_request_id: str
    issuer_validation_id: str
    verifier_id: str
    verifier_name: str
    receipt_notes: Optional[str] = None
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class VerifierReceiptCreate(BaseModel):
    transcript_request_id: str
    issuer_validation_id: str
    receipt_notes: Optional[str] = None

class UserSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    session_token: str
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Helper functions
def generate_content_hash(content: str) -> str:
    """Generate SHA-256 hash for document content integrity"""
    return hashlib.sha256(content.encode()).hexdigest()

async def get_current_user(request: Request) -> Optional[User]:
    """Get current user from session token in cookies or headers"""
    session_token = None
    
    # Check cookies first
    if "session_token" in request.cookies:
        session_token = request.cookies["session_token"]
    # Fallback to Authorization header
    elif "authorization" in request.headers:
        auth_header = request.headers["authorization"]
        if auth_header.startswith("Bearer "):
            session_token = auth_header[7:]
    
    if not session_token:
        return None
    
    # Find session in database
    session = await db.user_sessions.find_one({"session_token": session_token})
    if not session or datetime.now(timezone.utc) > session["expires_at"]:
        return None
    
    # Get user
    user = await db.users.find_one({"id": session["user_id"]})
    if not user:
        return None
    
    return User(**user)

# Mock Authentication endpoints for testing
@api_router.post("/auth/mock-login")
async def mock_login(request: Request):
    """Mock login endpoint for testing - creates/gets user with specified role"""
    try:
        body = await request.json()
        email = body.get("email", "")
        name = body.get("name", "")
        role = body.get("role", "student")
        university = body.get("university", "")
        
        if not email or not name:
            raise HTTPException(status_code=400, detail="Email and name are required")
        
        # Check if user exists
        existing_user = await db.users.find_one({"email": email})
        user_data = None
        
        if existing_user:
            user_data = User(**existing_user)
            # Update role and university if provided
            if role or university:
                await db.users.update_one(
                    {"email": email},
                    {"$set": {"role": role, "university": university}}
                )
                user_data.role = UserRole(role)
                user_data.university = university
        else:
            # Create new user
            new_user = User(
                email=email,
                name=name,
                role=UserRole(role),
                university=university
            )
            await db.users.insert_one(new_user.dict())
            user_data = new_user
        
        # Create session
        session_token = str(uuid.uuid4())
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        session = UserSession(
            user_id=user_data.id,
            session_token=session_token,
            expires_at=expires_at
        )
        await db.user_sessions.insert_one(session.dict())
        
        return {
            "user": user_data.dict(),
            "session_token": session_token
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@api_router.get("/auth/session-data")
async def get_session_data(request: Request):
    """Process session_id from Emergent Auth and return user data - MOCK VERSION"""
    session_id = request.headers.get("X-Session-ID")
    if not session_id:
        raise HTTPException(status_code=400, detail="Session ID required")
    
    # Mock auth data - in real implementation this would call external service
    if session_id == "mock_session_123":
        auth_data = {
            "email": "john.student@university.edu",
            "name": "John Student",
            "picture": "https://via.placeholder.com/150",
            "session_token": str(uuid.uuid4())
        }
    else:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": auth_data["email"]})
    user_data = None
    
    if existing_user:
        user_data = User(**existing_user)
    else:
        # Create new user with default student role
        new_user = User(
            email=auth_data["email"],
            name=auth_data["name"],
            picture=auth_data.get("picture"),
            role=UserRole.STUDENT  # Default role
        )
        await db.users.insert_one(new_user.dict())
        user_data = new_user
    
    # Create session
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    session = UserSession(
        user_id=user_data.id,
        session_token=auth_data["session_token"],
        expires_at=expires_at
    )
    await db.user_sessions.insert_one(session.dict())
    
    return {
        "user": user_data.dict(),
        "session_token": auth_data["session_token"]
    }

@api_router.post("/auth/logout")
async def logout(request: Request, response: Response):
    """Logout user and clear session"""
    user = await get_current_user(request)
    if user:
        # Remove session from database
        session_token = request.cookies.get("session_token") or request.headers.get("authorization", "").replace("Bearer ", "")
        await db.user_sessions.delete_one({"session_token": session_token})
    
    # Clear cookie
    response.delete_cookie("session_token", path="/", secure=True, samesite="none")
    return {"message": "Logged out successfully"}

@api_router.get("/auth/me")
async def get_current_user_info(request: Request):
    """Get current user information"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user

# User role management
@api_router.put("/users/{user_id}/role")
async def update_user_role(user_id: str, role_data: dict, request: Request):
    """Update user role - admin functionality"""
    current_user = await get_current_user(request)
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Update user role
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"role": role_data["role"], "university": role_data.get("university")}}
    )
    return {"message": "Role updated successfully"}

# Transcript Request endpoints
@api_router.post("/transcript-requests", response_model=TranscriptRequest)
async def create_transcript_request(request_data: TranscriptRequestCreate, request: Request):
    """Student creates a transcript request"""
    user = await get_current_user(request)
    if not user or user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only students can create transcript requests")
    
    # Generate content hash
    content_hash = generate_content_hash(request_data.content)
    
    # Create transcript request
    transcript_request = TranscriptRequest(
        student_id=user.id,
        student_name=user.name,
        student_email=user.email,
        university_from=request_data.university_from,
        university_to=request_data.university_to,
        document_type=request_data.document_type,
        content_hash=content_hash
    )
    
    await db.transcript_requests.insert_one(transcript_request.dict())
    return transcript_request

@api_router.get("/transcript-requests", response_model=List[TranscriptRequest])
async def get_transcript_requests(request: Request, status: Optional[str] = None):
    """Get transcript requests based on user role"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    query = {}
    if status:
        query["status"] = status
    
    if user.role == UserRole.STUDENT:
        query["student_id"] = user.id
    elif user.role == UserRole.ISSUER:
        query["university_from"] = user.university
    elif user.role == UserRole.VERIFIER:
        query["university_to"] = user.university
    
    requests = await db.transcript_requests.find(query).to_list(100)
    return [TranscriptRequest(**req) for req in requests]

@api_router.get("/transcript-requests/{request_id}")
async def get_transcript_request_details(request_id: str, request: Request):
    """Get detailed transcript request with full audit trail"""
    user = await get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Get transcript request
    transcript_req = await db.transcript_requests.find_one({"id": request_id})
    if not transcript_req:
        raise HTTPException(status_code=404, detail="Request not found")
    
    # Get validation if exists
    validation = await db.issuer_validations.find_one({"transcript_request_id": request_id})
    
    # Get receipt if exists
    receipt = await db.verifier_receipts.find_one({"transcript_request_id": request_id})
    
    return {
        "transcript_request": TranscriptRequest(**transcript_req),
        "validation": IssuerValidation(**validation) if validation else None,
        "receipt": VerifierReceipt(**receipt) if receipt else None
    }

# Issuer Validation endpoints
@api_router.post("/issuer-validations", response_model=IssuerValidation)
async def create_issuer_validation(validation_data: IssuerValidationCreate, request: Request):
    """Issuer validates a transcript request"""
    user = await get_current_user(request)
    if not user or user.role != UserRole.ISSUER:
        raise HTTPException(status_code=403, detail="Only issuers can validate requests")
    
    # Check if request exists and belongs to issuer's university
    transcript_req = await db.transcript_requests.find_one({"id": validation_data.transcript_request_id})
    if not transcript_req:
        raise HTTPException(status_code=404, detail="Transcript request not found")
    
    if transcript_req["university_from"] != user.university:
        raise HTTPException(status_code=403, detail="Cannot validate requests from other universities")
    
    # Create validation
    validation = IssuerValidation(
        transcript_request_id=validation_data.transcript_request_id,
        issuer_id=user.id,
        issuer_name=user.name,
        validation_notes=validation_data.validation_notes,
        is_approved=validation_data.is_approved
    )
    
    await db.issuer_validations.insert_one(validation.dict())
    
    # Update transcript request status
    new_status = RequestStatus.VALIDATED if validation_data.is_approved else RequestStatus.REJECTED
    await db.transcript_requests.update_one(
        {"id": validation_data.transcript_request_id},
        {"$set": {"status": new_status}}
    )
    
    return validation

# Verifier Receipt endpoints
@api_router.post("/verifier-receipts", response_model=VerifierReceipt)
async def create_verifier_receipt(receipt_data: VerifierReceiptCreate, request: Request):
    """Verifier acknowledges receipt of validated transcript"""
    user = await get_current_user(request)
    if not user or user.role != UserRole.VERIFIER:
        raise HTTPException(status_code=403, detail="Only verifiers can create receipts")
    
    # Check if request exists and is validated
    transcript_req = await db.transcript_requests.find_one({"id": receipt_data.transcript_request_id})
    if not transcript_req:
        raise HTTPException(status_code=404, detail="Transcript request not found")
    
    if transcript_req["university_to"] != user.university:
        raise HTTPException(status_code=403, detail="Cannot receive requests for other universities")
    
    if transcript_req["status"] != RequestStatus.VALIDATED:
        raise HTTPException(status_code=400, detail="Request must be validated before receipt")
    
    # Create receipt
    receipt = VerifierReceipt(
        transcript_request_id=receipt_data.transcript_request_id,
        issuer_validation_id=receipt_data.issuer_validation_id,
        verifier_id=user.id,
        verifier_name=user.name,
        receipt_notes=receipt_data.receipt_notes
    )
    
    await db.verifier_receipts.insert_one(receipt.dict())
    
    # Update transcript request status
    await db.transcript_requests.update_one(
        {"id": receipt_data.transcript_request_id},
        {"$set": {"status": RequestStatus.RECEIVED}}
    )
    
    return receipt

# UUID Verification endpoint
@api_router.get("/verify/{uuid_type}/{uuid_value}")
async def verify_uuid(uuid_type: str, uuid_value: str):
    """Verify UUID authenticity and get associated data"""
    if uuid_type == "student_request":
        doc = await db.transcript_requests.find_one({"student_request_uuid": uuid_value})
        if doc:
            return {"type": "student_request", "data": TranscriptRequest(**doc), "verified": True}
    elif uuid_type == "issuer_validation":
        doc = await db.issuer_validations.find_one({"issuer_validation_uuid": uuid_value})
        if doc:
            return {"type": "issuer_validation", "data": IssuerValidation(**doc), "verified": True}
    elif uuid_type == "verifier_receipt":
        doc = await db.verifier_receipts.find_one({"verifier_receipt_uuid": uuid_value})
        if doc:
            return {"type": "verifier_receipt", "data": VerifierReceipt(**doc), "verified": True}
    
    return {"verified": False, "message": "UUID not found or invalid"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()