from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Receivable(Base):
    __tablename__ = "receivables"

    id = Column(Integer, primary_key=True)
    expense_id = Column(Integer, ForeignKey("expense_records.id", ondelete="CASCADE"), index=True, nullable=False)
    person_name = Column(String(80), index=True, nullable=False)
    amount = Column(Integer, nullable=False)
    status = Column(String(20), default="pending", index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    settled_at = Column(DateTime(timezone=True), nullable=True)

    expense = relationship("ExpenseRecord", back_populates="receivables")
