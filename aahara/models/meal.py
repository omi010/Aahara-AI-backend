from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from aahara.database import Base

class Meal(Base):
    __tablename__ = "meals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    food_name = Column(String)
    calories = Column(Integer)
    protein = Column(Float)
    carbs = Column(Float)
    fat = Column(Float)
    created_at = Column(DateTime(timezone=True), server_default=func.now())