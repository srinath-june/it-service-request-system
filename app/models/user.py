from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.models.enums import UserRole

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(SAEnum(UserRole, native_enum=False, values_callable=lambda x: [e.value for e in x]), default=UserRole.EMPLOYEE, nullable=False)
    department = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    requested_tickets = relationship("ServiceRequest", foreign_keys="[ServiceRequest.requester_id]", back_populates="requester")
    assigned_tickets = relationship("ServiceRequest", foreign_keys="[ServiceRequest.assigned_to_id]", back_populates="assigned_to")
    resolved_tickets = relationship("ServiceRequest", foreign_keys="[ServiceRequest.resolved_by_id]", back_populates="resolved_by")
    comments = relationship("RequestComment", back_populates="author")
    history_records = relationship("RequestHistory", back_populates="actor")
