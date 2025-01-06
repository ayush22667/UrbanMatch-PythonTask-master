from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from database import SessionLocal, engine, Base
import models, schemas
from typing import List
import re
from sqlalchemy import or_,func, and_

app = FastAPI()

# Email validation function
def validate_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

# Create database tables
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"message": "Welcome to the Marriage Matchmaking API"}

# Create User Endpoint with email validation
@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    if not validate_email(user.email):
        raise HTTPException(status_code=400, detail="Invalid email format")
    
    existing_user = db.query(models.User).filter(models.User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
   
    user_dict = user.dict()
    user_dict["interests"] = ",".join(user_dict["interests"])
    
    # Create the user
    db_user = models.User(**user_dict)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Read All Users Endpoint
@app.get("/users/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

# Read User by ID Endpoint
@app.get("/users/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Update User Endpoint
@app.put("/users/{user_id}", response_model=schemas.User)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = user.model_dump(exclude_unset=True)
    
    # Convert interests list to a comma-separated string if it's being updated
    if 'interests' in update_data and update_data['interests'] is not None:
        update_data['interests'] = ",".join(update_data['interests'])
    
    # Validate email if it's being updated
    if 'email' in update_data and update_data['email'] is not None:
        if not validate_email(update_data['email']):
            raise HTTPException(status_code=400, detail="Invalid email format")
        # Check if new email already exists for a different user
        existing_user = db.query(models.User).filter(
            models.User.email == update_data['email'],
            models.User.id != user_id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Update user fields
    db.query(models.User).filter(models.User.id == user_id).update(update_data)
    
    db.commit()
    db.refresh(db_user)
    return db_user

# Delete User Endpoint
@app.delete("/users/{user_id}", response_model=schemas.User)
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    return db_user

# Find Matches for a User Endpoint
@app.get("/users/{user_id}/matches", response_model=List[schemas.User])
def find_matches(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get user interests as a list
    user_interests = db_user.interests.split(",")
    

    matches = db.query(models.User).filter(
        models.User.city == db_user.city,
        or_(*[models.User.interests.like(f"%{interest}%") for interest in user_interests]),
        func.lower(models.User.gender) != func.lower(db_user.gender),
        and_(
            models.User.age >= db_user.age - 10,
            models.User.age <= db_user.age + 10  
        )
    ).all()
    
    return matches
