from sqlalchemy import Column, Integer, Float, Boolean, DateTime, Enum as SAEnum
from datetime import datetime
from app.database import Base
from app.models.enums import Priority

class SLAConfig(Base):
    __tablename__ = "sla_configs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    priority = Column(SAEnum(Priority, native_enum=False, values_callable=lambda x: [e.value for e in x]), unique=True, index=True, nullable=False)
    resolution_sla_hours = Column(Float, nullable=False)
    response_sla_hours = Column(Float, default=1.0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
