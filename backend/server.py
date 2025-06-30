from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pymongo import MongoClient
from datetime import datetime, timedelta, timezone
import os
import uuid
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import json
import bcrypt
from supabase import create_client, Client
import asyncio
from apscheduler.schedulers.background import BackgroundScheduler
import atexit
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv('/app/backend/.env')

app = FastAPI(title="RevMix API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB setup
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'revmix_production')

# Supabase setup
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')
SUPABASE_SERVICE_KEY = os.environ.get('SUPABASE_SERVICE_KEY')

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
security = HTTPBearer()

client = MongoClient(MONGO_URL)
db = client[DB_NAME]

# Collections
users_collection = db.users
rooms_collection = db.rooms
performances_collection = db.performances
votes_collection = db.votes
challenges_collection = db.challenges
audio_effects_collection = db.audio_effects

# Pydantic models
class User(BaseModel):
    id: str
    username: str
    email: str
    avatar_url: str = "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&h=150&fit=crop&crop=face"
    level: int = 1
    xp: int = 0
    bio: str = ""
    badges: List[str] = []
    wins: int = 0
    battles: int = 0
    created_at: datetime
    supabase_id: str

class Room(BaseModel):
    id: str
    name: str
    host_id: str
    type: str  # solo, collab, challenge
    prompt: str
    participants: List[str] = []
    status: str = "waiting"  # waiting, active, judging, completed, closed
    created_at: datetime
    expires_at: datetime  # 1 hour from creation
    timer_duration: int = 300  # 5 minutes in seconds
    max_participants: int = 10
    results_announced: bool = False
    winner_id: Optional[str] = None

class Performance(BaseModel):
    id: str
    user_id: str
    username: str
    room_id: str
    audio_data: str  # base64 audio data
    duration: float
    timeline_marks: List[float] = []
    audio_timeline: List[Dict[str, Any]] = []  # For multi-track audio
    submitted_at: datetime
    votes: Dict[str, Dict[str, int]] = {}  # {user_id: {flow: int, lyrics: int, creativity: int}}
    average_score: float = 0.0
    vote_count: int = 0

class Vote(BaseModel):
    id: str
    voter_id: str
    voter_username: str
    performance_id: str
    room_id: str
    flow: int  # 1-10
    lyrics: int  # 1-10
    creativity: int  # 1-10
    emoji_reaction: str = "🔥"
    created_at: datetime

class Challenge(BaseModel):
    id: str
    title: str
    description: str
    creator_id: str
    type: str  # public, private
    rules: dict
    participants: List[str] = []
    created_at: datetime
    starts_at: datetime
    status: str = "upcoming"  # upcoming, active, completed

class AudioEffect(BaseModel):
    id: str
    name: str
    category: str  # "builtin" or "custom"
    audio_data: str  # base64 audio data
    duration: float
    created_by: Optional[str] = None
    created_at: datetime

class LoginRequest(BaseModel):
    username: str
    password: str

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

# Authentication functions
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        
        # Handle test user tokens
        if token.startswith("test_token_"):
            user_id = token.replace("test_token_", "")
            db_user = users_collection.find_one({"id": user_id, "is_test_user": True})
            if db_user:
                db_user.pop('_id', None)
                return db_user
            else:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid test token",
                )
        
        # Regular Supabase authentication
        user = supabase.auth.get_user(token)
        
        if not user or not user.user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Get user from our database
        db_user = users_collection.find_one({"supabase_id": user.user.id})
        if not db_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found in database",
            )
        
        db_user.pop('_id', None)
        return db_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Room cleanup scheduler
scheduler = BackgroundScheduler()

def cleanup_expired_rooms():
    """Remove expired rooms and announce results"""
    try:
        current_time = datetime.now(timezone.utc)
        expired_rooms = list(rooms_collection.find({
            "expires_at": {"$lt": current_time},
            "status": {"$ne": "closed"}
        }))
        
        for room in expired_rooms:
            # Announce results if not already done
            if not room.get("results_announced", False):
                announce_room_results(room["id"])
            
            # Mark room as closed
            rooms_collection.update_one(
                {"id": room["id"]},
                {"$set": {"status": "closed", "results_announced": True}}
            )
        
        if len(expired_rooms) > 0:
            print(f"Cleaned up {len(expired_rooms)} expired rooms")
    except Exception as e:
        print(f"Error cleaning up rooms: {e}")

def announce_room_results(room_id: str):
    """Calculate and announce room results"""
    try:
        # Get all performances for this room
        performances = list(performances_collection.find({"room_id": room_id}))
        
        if not performances:
            return
        
        # Sort by average score
        performances.sort(key=lambda x: x.get("average_score", 0), reverse=True)
        
        # Update winner
        if performances:
            winner = performances[0]
            rooms_collection.update_one(
                {"id": room_id},
                {
                    "$set": {
                        "winner_id": winner["user_id"],
                        "results_announced": True
                    }
                }
            )
            
            # Award XP to winner
            users_collection.update_one(
                {"id": winner["user_id"]},
                {
                    "$inc": {"xp": 100, "wins": 1, "battles": 1},
                    "$push": {"badges": "Battle Winner"}
                }
            )
            
            # Award XP to participants
            for perf in performances[1:]:
                users_collection.update_one(
                    {"id": perf["user_id"]},
                    {"$inc": {"xp": 25, "battles": 1}}
                )
        
        print(f"Results announced for room {room_id}")
    except Exception as e:
        print(f"Error announcing results for room {room_id}: {e}")

# Start scheduler
scheduler.add_job(cleanup_expired_rooms, 'interval', minutes=5)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

# Initialize database and create built-in effects
@app.on_event("startup")
async def startup_event():
    # Create indexes for better performance
    users_collection.create_index("id", unique=True)
    users_collection.create_index("username", unique=True)
    users_collection.create_index("supabase_id", unique=True)
    rooms_collection.create_index("id", unique=True)
    rooms_collection.create_index("expires_at")
    performances_collection.create_index("room_id")
    performances_collection.create_index("user_id")
    votes_collection.create_index("performance_id")
    votes_collection.create_index([("voter_id", 1), ("performance_id", 1)], unique=True)
    challenges_collection.create_index("id", unique=True)
    audio_effects_collection.create_index("id", unique=True)
    
    # Clear existing data (as requested)
    users_collection.delete_many({})
    rooms_collection.delete_many({})
    performances_collection.delete_many({})
    votes_collection.delete_many({})
    challenges_collection.delete_many({})
    
    # Create built-in audio effects
    builtin_effects = [
        {
            "id": str(uuid.uuid4()),
            "name": "Boom",
            "category": "builtin",
            "audio_data": "UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUX7Xqz6hVFQlLH", 
            "duration": 0.5,
            "created_by": None,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Applause",
            "category": "builtin", 
            "audio_data": "UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUX7Xqz6hVFQlLH",
            "duration": 1.0,
            "created_by": None, 
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Air Horn",
            "category": "builtin",
            "audio_data": "UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUX7Xqz6hVFQlLH",
            "duration": 0.8,
            "created_by": None,
            "created_at": datetime.now(timezone.utc)
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Vinyl Scratch",
            "category": "builtin",
            "audio_data": "UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUX7Xqz6hVFQlLH",
            "duration": 0.3,
            "created_by": None,
            "created_at": datetime.now(timezone.utc)
        }
    ]
    
    for effect in builtin_effects:
        audio_effects_collection.insert_one(effect)
    
    print("Database initialized with indexes and built-in effects")

# API Routes
@app.get("/api/")
async def root():
    return {"message": "RevMix API is running! 🎤"}

# Authentication routes
@app.post("/api/auth/register")
async def register(request: RegisterRequest):
    try:
        # Check if username already exists
        existing_user = users_collection.find_one({"username": request.username})
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        
        # Create user in Supabase
        auth_response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password,
            "options": {
                "data": {
                    "username": request.username
                }
            }
        })
        
        if auth_response.user:
            # Create user in our database
            new_user = {
                "id": str(uuid.uuid4()),
                "username": request.username,
                "email": request.email,
                "supabase_id": auth_response.user.id,
                "avatar_url": "https://images.unsplash.com/photo-1535713875002-d1d0cf377fde?w=150&h=150&fit=crop&crop=face",
                "level": 1,
                "xp": 0,
                "bio": "New to the scene 🎤",
                "badges": ["Newcomer"],
                "wins": 0,
                "battles": 0,
                "created_at": datetime.now(timezone.utc)
            }
            users_collection.insert_one(new_user)
            new_user.pop('_id', None)
            
            return {
                "user": new_user,
                "session": auth_response.session
            }
        else:
            raise HTTPException(status_code=400, detail="Registration failed")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/auth/login")  
async def login(request: LoginRequest):
    try:
        # Get user from database
        db_user = users_collection.find_one({"username": request.username})
        if not db_user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Handle test users (Admin) without Supabase
        if db_user.get("is_test_user") and request.username == "Admin" and request.password == "admin123":
            # Create a mock session for test user
            mock_session = {
                "access_token": f"test_token_{db_user['id']}",
                "token_type": "bearer",
                "expires_in": 3600,
                "user": {
                    "id": db_user["id"],
                    "email": db_user["email"],
                    "username": db_user["username"]
                }
            }
            
            db_user.pop('_id', None)
            return {
                "user": db_user,
                "session": mock_session
            }
        
        # Regular Supabase login for other users
        auth_response = supabase.auth.sign_in_with_password({
            "email": db_user["email"],
            "password": request.password
        })
        
        if auth_response.user and auth_response.session:
            db_user.pop('_id', None)
            return {
                "user": db_user,
                "session": auth_response.session
            }
        else:
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
    except Exception as e:
        # For test user, provide more specific error handling
        if request.username == "Admin":
            if request.password != "admin123":
                raise HTTPException(status_code=401, detail="Invalid password for Admin user")
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/api/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# User routes
@app.get("/api/users/profile/{user_id}")
async def get_user_profile(user_id: str):
    user = users_collection.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.pop('_id', None)
    return user

@app.get("/api/users/me")
async def get_current_user_profile(current_user: dict = Depends(get_current_user)):
    return current_user

@app.get("/api/users/leaderboard")
async def get_leaderboard(limit: int = 10):
    users = list(users_collection.find({}, {"_id": 0}).sort("xp", -1).limit(limit))
    return {"leaderboard": users}

# Room routes
@app.get("/api/rooms")
async def get_rooms():
    current_time = datetime.now(timezone.utc)
    # Only get active rooms (not expired or closed)
    rooms = list(rooms_collection.find({
        "expires_at": {"$gt": current_time},
        "status": {"$ne": "closed"}
    }, {"_id": 0}))
    return {"rooms": rooms}

@app.get("/api/rooms/{room_id}")
async def get_room(room_id: str):
    room = rooms_collection.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    room.pop('_id', None)
    return room

@app.post("/api/rooms")
async def create_room(room_data: dict, current_user: dict = Depends(get_current_user)):
    room_id = str(uuid.uuid4())
    expires_at = datetime.now(timezone.utc) + timedelta(hours=1)  # 1 hour from now
    
    new_room = {
        "id": room_id,
        "name": room_data.get("name", "New Battle Room"),
        "host_id": current_user["id"],
        "type": room_data.get("type", "challenge"),
        "prompt": room_data.get("prompt", "Show us what you got!"),
        "participants": [current_user["id"]],
        "status": "waiting",
        "created_at": datetime.now(timezone.utc),
        "expires_at": expires_at,
        "timer_duration": room_data.get("timer_duration", 300),
        "max_participants": room_data.get("max_participants", 10),
        "results_announced": False,
        "winner_id": None
    }
    rooms_collection.insert_one(new_room)
    new_room.pop('_id', None)
    return new_room

@app.post("/api/rooms/{room_id}/join")
async def join_room(room_id: str, current_user: dict = Depends(get_current_user)):
    room = rooms_collection.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Check if room is still active
    if room["expires_at"] < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Room has expired")
    
    if room["status"] == "closed":
        raise HTTPException(status_code=400, detail="Room is closed")
    
    if current_user["id"] not in room["participants"]:
        if len(room["participants"]) >= room["max_participants"]:
            raise HTTPException(status_code=400, detail="Room is full")
            
        rooms_collection.update_one(
            {"id": room_id},
            {"$push": {"participants": current_user["id"]}}
        )
    
    return {"message": "Joined room successfully"}

# Performance routes  
@app.post("/api/performances")
async def submit_performance(performance_data: dict, current_user: dict = Depends(get_current_user)):
    performance_id = str(uuid.uuid4())
    new_performance = {
        "id": performance_id,
        "user_id": current_user["id"],
        "username": current_user["username"],
        "room_id": performance_data.get("room_id"),
        "audio_data": performance_data.get("audio_data"),
        "duration": performance_data.get("duration", 0),
        "timeline_marks": performance_data.get("timeline_marks", []),
        "audio_timeline": performance_data.get("audio_timeline", []),
        "submitted_at": datetime.now(timezone.utc),
        "votes": {},
        "average_score": 0.0,
        "vote_count": 0
    }
    performances_collection.insert_one(new_performance)
    new_performance.pop('_id', None)
    return new_performance

@app.get("/api/performances/room/{room_id}")
async def get_room_performances(room_id: str):
    performances = list(performances_collection.find({"room_id": room_id}, {"_id": 0}).sort("average_score", -1))
    return {"performances": performances}

# Voting routes
@app.post("/api/votes")
async def submit_vote(vote_data: dict, current_user: dict = Depends(get_current_user)):
    performance_id = vote_data.get("performance_id")
    
    # Check if user already voted for this performance
    existing_vote = votes_collection.find_one({
        "voter_id": current_user["id"],
        "performance_id": performance_id
    })
    
    if existing_vote:
        raise HTTPException(status_code=400, detail="You have already voted for this performance")
    
    # Check if user is trying to vote for their own performance
    performance = performances_collection.find_one({"id": performance_id})
    if performance and performance["user_id"] == current_user["id"]:
        raise HTTPException(status_code=400, detail="You cannot vote for your own performance")
    
    vote_id = str(uuid.uuid4())
    new_vote = {
        "id": vote_id,
        "voter_id": current_user["id"],
        "voter_username": current_user["username"],
        "performance_id": performance_id,
        "room_id": vote_data.get("room_id"),
        "flow": vote_data.get("flow", 5),
        "lyrics": vote_data.get("lyrics", 5),
        "creativity": vote_data.get("creativity", 5),
        "emoji_reaction": vote_data.get("emoji_reaction", "🔥"),
        "created_at": datetime.now(timezone.utc)
    }
    votes_collection.insert_one(new_vote)
    
    # Update performance with new vote
    if performance:
        votes = performance.get("votes", {})
        votes[current_user["id"]] = {
            "flow": vote_data.get("flow"),
            "lyrics": vote_data.get("lyrics"),
            "creativity": vote_data.get("creativity")
        }
        
        # Calculate average score
        total_votes = len(votes)
        if total_votes > 0:
            avg_flow = sum(v["flow"] for v in votes.values()) / total_votes
            avg_lyrics = sum(v["lyrics"] for v in votes.values()) / total_votes
            avg_creativity = sum(v["creativity"] for v in votes.values()) / total_votes
            average_score = (avg_flow + avg_lyrics + avg_creativity) / 3
        else:
            average_score = 0.0
            
        performances_collection.update_one(
            {"id": performance_id},
            {"$set": {
                "votes": votes, 
                "average_score": average_score,
                "vote_count": total_votes
            }}
        )
    
    new_vote.pop('_id', None)
    return new_vote

@app.get("/api/votes/performance/{performance_id}")
async def get_performance_votes(performance_id: str):
    votes = list(votes_collection.find({"performance_id": performance_id}, {"_id": 0}))
    return {"votes": votes}

# Audio effects routes
@app.get("/api/audio-effects")
async def get_audio_effects():
    effects = list(audio_effects_collection.find({}, {"_id": 0}))
    return {"effects": effects}

@app.post("/api/audio-effects")
async def create_audio_effect(effect_data: dict, current_user: dict = Depends(get_current_user)):
    effect_id = str(uuid.uuid4())
    new_effect = {
        "id": effect_id,
        "name": effect_data.get("name"),
        "category": "custom",
        "audio_data": effect_data.get("audio_data"),
        "duration": effect_data.get("duration", 0),
        "created_by": current_user["id"],
        "created_at": datetime.now(timezone.utc)
    }
    audio_effects_collection.insert_one(new_effect)
    new_effect.pop('_id', None)
    return new_effect

# Challenge routes
@app.get("/api/challenges")
async def get_challenges():
    challenges = list(challenges_collection.find({}, {"_id": 0}))
    return {"challenges": challenges}

@app.post("/api/challenges")
async def create_challenge(challenge_data: dict, current_user: dict = Depends(get_current_user)):
    challenge_id = str(uuid.uuid4())
    new_challenge = {
        "id": challenge_id,
        "title": challenge_data.get("title", "New Challenge"),
        "description": challenge_data.get("description", ""),
        "creator_id": current_user["id"],
        "type": challenge_data.get("type", "public"),
        "rules": challenge_data.get("rules", {}),
        "participants": [current_user["id"]],
        "created_at": datetime.now(timezone.utc),
        "starts_at": datetime.now(timezone.utc) + timedelta(hours=1),
        "status": "upcoming"
    }
    challenges_collection.insert_one(new_challenge)
    new_challenge.pop('_id', None)
    return new_challenge

# Room results and cleanup
@app.get("/api/rooms/{room_id}/results")
async def get_room_results(room_id: str):
    room = rooms_collection.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    performances = list(performances_collection.find(
        {"room_id": room_id}, 
        {"_id": 0}
    ).sort("average_score", -1))
    
    return {
        "room": {k: v for k, v in room.items() if k != '_id'},
        "performances": performances,
        "results_announced": room.get("results_announced", False),
        "winner_id": room.get("winner_id")
    }

@app.post("/api/rooms/{room_id}/close")
async def close_room(room_id: str, current_user: dict = Depends(get_current_user)):
    room = rooms_collection.find_one({"id": room_id})
    if not room:
        raise HTTPException(status_code=404, detail="Room not found")
    
    # Only room host can close the room
    if room["host_id"] != current_user["id"]:
        raise HTTPException(status_code=403, detail="Only the room host can close the room")
    
    # Announce results if not already done
    if not room.get("results_announced", False):
        announce_room_results(room_id)
    
    # Mark room as closed
    rooms_collection.update_one(
        {"id": room_id},
        {"$set": {"status": "closed", "results_announced": True}}
    )
    
    return {"message": "Room closed successfully"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)