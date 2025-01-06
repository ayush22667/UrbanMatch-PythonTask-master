from pydantic import BaseModel, field_validator
from typing import List, Optional

class UserBase(BaseModel):
    name: str
    age: int
    gender: str
    email: str 
    city: str
    interests: List[str] 

    # Convert list to comma-separated string before saving to the database
    @field_validator("interests", mode="before")
    def join_interests(cls, v):
        if isinstance(v, str):
            return v.split(",") 
        return v

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    interests: Optional[List[str]] = None

    # Convert list to comma-separated string before saving to the database
    @field_validator("interests", mode="before")
    def join_interests(cls, v):
        if isinstance(v, str):
            return v.split(",") 
        return v

class User(UserBase):
    id: int

    # Convert comma-separated string back to list when retrieving from the database
    @field_validator("interests", mode="before")
    def split_interests(cls, v):
        if isinstance(v, str):
            return v.split(",")
        return v

    class Config:
        from_attributes = True