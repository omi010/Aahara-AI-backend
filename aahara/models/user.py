from sqlalchemy import Column, Integer, String
from aahara.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    daily_goal = Column(Integer, default=2000)
    height_cm = Column(Integer, nullable=True)
    weight_kg = Column(Integer, nullable=True)