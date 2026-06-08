from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
 
from app.database.db import Base
 
 
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
 
    id          = Column(String(36), primary_key=True)  # UUID as string
    user_id     = Column(String(20), ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False)
    token_hash  = Column(String(255), nullable=False, unique=True)  # store hash not raw token
    is_revoked  = Column(Boolean, default=False)
    expires_at  = Column(DateTime(timezone=True), nullable=False)
    created_at  = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
 
    # Relationship back to User
    user = relationship("User", back_populates="refresh_tokens")
 
    def __repr__(self):
        return f"<RefreshToken user_id={self.user_id} revoked={self.is_revoked}>"