from sqlalchemy import Column, Integer, String, ForeignKey, Date
from sqlalchemy.orm import relationship
from aahara.database import Base
from datetime import date


class FoodLog(Base):
    __tablename__ = "food_logs"

    id = Column(Integer, primary_key=True, index=True)
    food_name = Column(String, nullable=False)
    calories = Column(Integer, nullable=False)
    quantity = Column(String, nullable=False)
    meal_type = Column(String, nullable=False)  # breakfast/lunch/dinner/snacks
    log_date = Column(Date, default=date.today)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")