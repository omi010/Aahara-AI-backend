from sqlalchemy import Column, Integer, ForeignKey, Date
from sqlalchemy.orm import relationship
from aahara.database import Base
from datetime import date


class WeightLog(Base):
    __tablename__ = "weight_logs"

    id = Column(Integer, primary_key=True, index=True)
    weight_kg = Column(Integer, nullable=False)
    log_date = Column(Date, default=date.today)

    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User")