from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class WeaponPattern(BaseModel):
    hash_id: int
    name: str
    progress: int
    completion_value: int
    is_completed: bool

class WeaponPatternDB(Base):
    __tablename__ = "weapon_patterns"

    id = Column(Integer, primary_key=True, index=True)
    hash_id = Column(Integer, unique=True, index=True)
    name = Column(String, index=True)
    progress = Column(Integer, default=0)
    completion_value = Column(Integer, default=5)
    is_completed = Column(Boolean, default=False)

