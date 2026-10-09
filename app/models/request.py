from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Enum as SAEnum, Float, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
from app.models.enums import Priority, RequestStatus

class ServiceRequest(Base):
    __tablename__ = "service_requests"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    request_number = Column(String(30), unique=True, index=True, nullable=False)
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    category_id = Column(Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    priority = Column(SAEnum(Priority, native_enum=False, values_callable=lambda x: [e.value for e in x]), default=Priority.MEDIUM, nullable=False, index=True)
    status = Column(SAEnum(RequestStatus, native_enum=False, values_callable=lambda x: [e.value for e in x]), default=RequestStatus.NEW, nullable=False, index=True)

    requester_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    assigned_to_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # Resolution & Closure Info
    resolution_details = Column(Text, nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    closed_at = Column(DateTime, nullable=True)
    reopened_at = Column(DateTime, nullable=True)

    # SLA Tracking Fields
    sla_target_hours = Column(Float, nullable=False)
    sla_due_at = Column(DateTime, nullable=False, index=True)
    total_on_hold_seconds = Column(Integer, default=0, nullable=False)
    on_hold_started_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    category = relationship("Category", back_populates="requests")
    requester = relationship("User", foreign_keys=[requester_id], back_populates="requested_tickets")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id], back_populates="assigned_tickets")
    resolved_by = relationship("User", foreign_keys=[resolved_by_id], back_populates="resolved_tickets")
    comments = relationship("RequestComment", back_populates="request", cascade="all, delete-orphan", order_by="RequestComment.created_at.desc()")
    history = relationship("RequestHistory", back_populates="request", cascade="all, delete-orphan", order_by="RequestHistory.created_at.desc()")

    __table_args__ = (
        Index("ix_requests_status_priority", "status", "priority"),
        Index("ix_requests_assigned_status", "assigned_to_id", "status"),
        Index("ix_requests_requester_status", "requester_id", "status"),
    )
