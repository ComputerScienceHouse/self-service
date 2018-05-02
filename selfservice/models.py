from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Date, Boolean, func
from datetime import datetime, timedelta
from selfservice import db


class ResetToken(db.Model):
    __tablename__ = 'token'
    id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=False)
    created = Column(DateTime, default=func.current_timestamp())

