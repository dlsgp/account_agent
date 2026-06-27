from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ExpenseRecord(Base):
    __tablename__ = "expense_records"

    id = Column(Integer, primary_key=True)
    date = Column(Date, index=True, nullable=False)
    title = Column(String(120), nullable=False)
    category = Column(String(40), index=True, nullable=False)
    payment_amount = Column(Integer, nullable=False)
    my_share = Column(Integer, nullable=False)
    people_count = Column(Integer, nullable=True)
    paid_by_me = Column(Boolean, nullable=False)
    receivable_amount = Column(Integer, default=0, nullable=False)
    payable_amount = Column(Integer, default=0, nullable=False)
    type = Column(String(20), default="expense", nullable=False)
    memo = Column(Text, nullable=True)
    raw_input = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    receivables = relationship("Receivable", back_populates="expense", cascade="all, delete-orphan")
