from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(255), default='')
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    memberships = relationship('OrganizationMember', back_populates='user')


class Organization(Base):
    __tablename__ = 'organizations'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    members = relationship('OrganizationMember', back_populates='organization')
    brand_profile = relationship('BrandProfile', back_populates='organization', uselist=False)


class OrganizationMember(Base):
    __tablename__ = 'organization_members'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey('organizations.id'), index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'), index=True)
    role: Mapped[str] = mapped_column(String(50), default='owner')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship('User', back_populates='memberships')
    organization = relationship('Organization', back_populates='members')


class BrandProfile(Base):
    __tablename__ = 'brand_profiles'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey('organizations.id'), unique=True, index=True)
    company_name: Mapped[str] = mapped_column(String(255))
    industry: Mapped[str] = mapped_column(String(255), default='')
    target_audience: Mapped[str] = mapped_column(Text, default='')
    services: Mapped[str] = mapped_column(Text, default='')
    brand_voice: Mapped[str] = mapped_column(String(255), default='professional, executive-friendly, clear')
    brand_colors: Mapped[str] = mapped_column(String(255), default='#0B1220,#1F6FEB,#FFFFFF')
    positioning_statement: Mapped[str] = mapped_column(Text, default='')
    topics_to_focus: Mapped[list] = mapped_column(JSON, default=list)
    topics_to_avoid: Mapped[list] = mapped_column(JSON, default=list)
    preferred_hashtags: Mapped[list] = mapped_column(JSON, default=list)
    forbidden_words: Mapped[list] = mapped_column(JSON, default=list)
    default_post_time: Mapped[str] = mapped_column(String(10), default='09:00')
    timezone: Mapped[str] = mapped_column(String(64), default='Asia/Dubai')
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    organization = relationship('Organization', back_populates='brand_profile')


class SocialAccount(Base):
    __tablename__ = 'social_accounts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey('organizations.id'), index=True)
    platform: Mapped[str] = mapped_column(String(50), default='linkedin')
    account_name: Mapped[str] = mapped_column(String(255), default='')
    member_urn: Mapped[str] = mapped_column(String(255), default='')
    page_urn: Mapped[str] = mapped_column(String(255), default='')
    encrypted_access_token: Mapped[str] = mapped_column(Text, default='')
    encrypted_refresh_token: Mapped[str] = mapped_column(Text, default='')
    scopes: Mapped[str] = mapped_column(Text, default='')
    connection_status: Mapped[str] = mapped_column(String(50), default='pending')
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class GeneratedPost(Base):
    __tablename__ = 'generated_posts'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, ForeignKey('organizations.id'), index=True)
    title: Mapped[str] = mapped_column(String(500), default='')
    content: Mapped[str] = mapped_column(Text)
    image_title: Mapped[str] = mapped_column(String(255), default='')
    image_subtitle: Mapped[str] = mapped_column(String(500), default='')
    image_path: Mapped[str] = mapped_column(String(500), default='')
    topic: Mapped[str] = mapped_column(String(255), default='')
    status: Mapped[str] = mapped_column(String(50), default='draft')
    ai_metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    scheduled_time: Mapped[str] = mapped_column(String(50), default='')
    published_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    organization_id: Mapped[int] = mapped_column(Integer, index=True)
    user_id: Mapped[int] = mapped_column(Integer, index=True)
    action: Mapped[str] = mapped_column(String(255))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
