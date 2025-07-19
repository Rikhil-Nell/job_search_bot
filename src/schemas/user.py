from pydantic import BaseModel, Field

class UserProfile(BaseModel):
    first_name: str = ""
    last_name: str = ""
    availability: str = ""
    bio: str = ""
    role: str = ""
    city: str = "Not specified"
    country: str = "Not specified"
    skills: list[str] = Field(default_factory=list)

class ChatRequest(BaseModel): # <-- ChatRequest also goes here!
    user_id: str
    message: str