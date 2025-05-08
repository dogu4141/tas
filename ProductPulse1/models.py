from datetime import datetime
from app import db
from flask_login import UserMixin
from sqlalchemy import ForeignKey, Table, Column, Integer
from sqlalchemy.orm import relationship

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='driver')  # admin, moderator, driver
    license_plate = db.Column(db.String(20))  # Only for drivers
    is_active = db.Column(db.Boolean, default=True)
    work_status = db.Column(db.String(20), default='inactive')  # active, inactive, break
    current_location = db.Column(db.String(100))  # Şoförün güncel konumu
    employee_id = db.Column(db.String(20), unique=True)  # Çalışan numarası
    department = db.Column(db.String(50))  # Departman
    position = db.Column(db.String(50))  # Pozisyon
    hire_date = db.Column(db.Date)  # İşe başlama tarihi
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vehicle_entries = relationship("VehicleEntry", back_populates="driver")
    vehicle_exits = relationship("VehicleExit", back_populates="driver")
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}" if self.first_name and self.last_name else self.username
    
    @property
    def is_on_leave(self):
        from models import LeaveRequest  # Import içeri alındı
        # Çalışanın izinde olup olmadığını kontrol et
        active_leave = LeaveRequest.query.filter(
            LeaveRequest.employee_id == self.id,
            LeaveRequest.status == 'approved',
            LeaveRequest.start_date <= datetime.utcnow().date(),
            LeaveRequest.end_date >= datetime.utcnow().date()
        ).first()
        return active_leave is not None
    
    def check_current_shift(self):
        from models import Shift  # Import içeri alındı
        # Şu anki vardiyayı kontrol et
        now = datetime.utcnow()
        current_time = now.time()
        weekday = now.weekday()  # 0 = Pazartesi, 6 = Pazar
        
        current_shift = Shift.query.filter(
            Shift.employee_id == self.id,
            Shift.day_of_week == weekday,
            Shift.start_time <= current_time,
            Shift.end_time >= current_time
        ).first()
        
        return current_shift


class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    chassis_number = db.Column(db.String(20), unique=True, nullable=False)
    brand = db.Column(db.String(50), nullable=False)
    model = db.Column(db.String(50), nullable=False)
    license_plate = db.Column(db.String(20))
    year = db.Column(db.Integer)
    status = db.Column(db.String(20), default='active')  # active, inactive, maintenance
    created_date = db.Column(db.Date, default=datetime.utcnow().date())
    created_time = db.Column(db.Time, default=datetime.utcnow().time())
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    damages = relationship("Damage", back_populates="vehicle")
    entries = relationship("VehicleEntry", back_populates="vehicle")
    exits = relationship("VehicleExit", back_populates="vehicle")
    load_items = relationship("LoadItem", back_populates="vehicle")
    
    def __repr__(self):
        return f'<Vehicle {self.chassis_number}>'


class VehicleEntry(db.Model):
    __tablename__ = 'vehicle_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, ForeignKey('vehicles.id'), nullable=False)
    driver_id = db.Column(db.Integer, ForeignKey('users.id'))
    entry_time = db.Column(db.DateTime, default=datetime.utcnow)
    yard = db.Column(db.String(50))  # Loading yard/area
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="entries")
    driver = relationship("User", back_populates="vehicle_entries")
    
    def __repr__(self):
        return f'<VehicleEntry {self.id}>'


class VehicleExit(db.Model):
    __tablename__ = 'vehicle_exits'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, ForeignKey('vehicles.id'), nullable=False)
    driver_id = db.Column(db.Integer, ForeignKey('users.id'))
    exit_time = db.Column(db.DateTime, default=datetime.utcnow)
    destination = db.Column(db.String(100))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="exits")
    driver = relationship("User", back_populates="vehicle_exits")
    
    def __repr__(self):
        return f'<VehicleExit {self.id}>'


class DamageType(db.Model):
    __tablename__ = 'damage_types'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    damages = relationship("Damage", back_populates="damage_type")
    
    def __repr__(self):
        return f'<DamageType {self.name}>'


class Damage(db.Model):
    __tablename__ = 'damages'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.Integer, ForeignKey('vehicles.id'), nullable=False)
    damage_type_id = db.Column(db.Integer, ForeignKey('damage_types.id'), nullable=False)
    description = db.Column(db.Text, nullable=False)
    location_x = db.Column(db.String(255))  # JSON string of X coordinates
    location_y = db.Column(db.String(255))  # JSON string of Y coordinates
    group = db.Column(db.String(10))  # damage group from the form (35-56 values)
    damage_description = db.Column(db.String(10))  # damage description code (760-768 values)
    level = db.Column(db.String(10))  # damage level (1-6 values)
    severity = db.Column(db.String(20))  # minor, moderate, severe
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, repaired
    recorded_by = db.Column(db.Integer, ForeignKey('users.id'))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    vehicle = relationship("Vehicle", back_populates="damages")
    damage_type = relationship("DamageType", back_populates="damages")
    recorder = relationship("User")
    
    def __repr__(self):
        return f'<Damage {self.id}>'


class Delivery(db.Model):
    __tablename__ = 'deliveries'
    
    id = db.Column(db.Integer, primary_key=True)
    delivery_number = db.Column(db.String(20), unique=True, nullable=False)
    driver_id = db.Column(db.Integer, ForeignKey('users.id'))
    issue_date = db.Column(db.Date, nullable=False)
    issue_time = db.Column(db.Time, nullable=False)
    loading_yard = db.Column(db.String(50))
    status = db.Column(db.String(20), default='active')  # active, completed, cancelled
    is_read = db.Column(db.Boolean, default=False)  # Şoförün bildirimi okuyup okumadığı
    assigned_by = db.Column(db.Integer, ForeignKey('users.id'))  # Kim atadı
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    driver = relationship("User", foreign_keys=[driver_id])
    assigner = relationship("User", foreign_keys=[assigned_by])
    delivery_items = relationship("DeliveryItem", back_populates="delivery", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Delivery {self.delivery_number}>'


class DeliveryItem(db.Model):
    __tablename__ = 'delivery_items'
    
    id = db.Column(db.Integer, primary_key=True)
    delivery_id = db.Column(db.Integer, ForeignKey('deliveries.id'), nullable=False)
    chassis_number = db.Column(db.String(20), nullable=False)
    brand = db.Column(db.String(50))
    model = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    delivery = relationship("Delivery", back_populates="delivery_items")
    
    def __repr__(self):
        return f'<DeliveryItem {self.id}>'


class Load(db.Model):
    __tablename__ = 'loads'
    
    id = db.Column(db.Integer, primary_key=True)
    load_number = db.Column(db.String(20), unique=True, nullable=False)
    created_by = db.Column(db.Integer, ForeignKey('users.id'))
    destination = db.Column(db.String(100))
    status = db.Column(db.String(20), default='pending')  # pending, in_transit, delivered
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User")
    load_items = relationship("LoadItem", back_populates="load", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Load {self.load_number}>'


class LoadItem(db.Model):
    __tablename__ = 'load_items'
    
    id = db.Column(db.Integer, primary_key=True)
    load_id = db.Column(db.Integer, ForeignKey('loads.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, ForeignKey('vehicles.id'), nullable=False)
    position = db.Column(db.Integer)  # 1-8 position in the load
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    load = relationship("Load", back_populates="load_items")
    vehicle = relationship("Vehicle", back_populates="load_items")
    
    def __repr__(self):
        return f'<LoadItem {self.id}>'


class ActivityLog(db.Model):
    __tablename__ = 'activity_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'))
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(50))  # vehicle, damage, delivery, load
    entity_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    
    def __repr__(self):
        return f'<ActivityLog {self.id}>'

# Chat system models

# Many-to-many relationship between users and chat groups
chat_group_members = Table(
    'chat_group_members',
    db.Model.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('group_id', Integer, ForeignKey('chat_groups.id'), primary_key=True)
)

class ChatGroup(db.Model):
    """A group chat that can have multiple users as members"""
    __tablename__ = 'chat_groups'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    is_private = db.Column(db.Boolean, default=False)
    region = db.Column(db.String(100))  # Optional region identifier
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by], backref="created_chat_groups")
    members = relationship("User", secondary=chat_group_members, backref="chat_groups")
    messages = relationship("ChatMessage", back_populates="group", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<ChatGroup {self.name}>'

class ChatMessage(db.Model):
    """A message sent by a user in a chat group or directly to another user"""
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    group_id = db.Column(db.Integer, ForeignKey('chat_groups.id'))
    sender_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, ForeignKey('users.id'))  # For direct messages
    content = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    has_attachment = db.Column(db.Boolean, default=False)
    location_lat = db.Column(db.Float)  # For location sharing
    location_lng = db.Column(db.Float)  # For location sharing
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], backref="received_messages")
    group = relationship("ChatGroup", back_populates="messages")
    attachments = relationship("ChatAttachment", back_populates="message", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<ChatMessage id={self.id}>'

class ChatAttachment(db.Model):
    """Attachment files for chat messages"""
    __tablename__ = 'chat_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    message_id = db.Column(db.Integer, ForeignKey('chat_messages.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))  # e.g., image, document, video, audio
    file_size = db.Column(db.Integer)  # in bytes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    message = relationship("ChatMessage", back_populates="attachments")
    
    def __repr__(self):
        return f'<ChatAttachment {self.file_name}>'


# Çalışan Yönetim Sistemi Modelleri

class Shift(db.Model):
    """Çalışan vardiya sistemi"""
    __tablename__ = 'shifts'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0: Pazartesi, 6: Pazar
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship("User", foreign_keys=[employee_id], backref="shifts")
    creator = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<Shift {self.id} - Gün: {self.day_of_week}>'


class LeaveRequest(db.Model):
    """Çalışan izin talepleri"""
    __tablename__ = 'leave_requests'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    leave_type = db.Column(db.String(20), nullable=False)  # paid, unpaid, sick, etc.
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    approved_by = db.Column(db.Integer, ForeignKey('users.id'))
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship("User", foreign_keys=[employee_id], backref="leave_requests")
    approver = relationship("User", foreign_keys=[approved_by])
    
    def __repr__(self):
        return f'<LeaveRequest {self.id} - {self.start_date} to {self.end_date}>'


class EmployeeReport(db.Model):
    """Çalışan raporları"""
    __tablename__ = 'employee_reports'
    
    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, ForeignKey('users.id'), nullable=False)
    report_date = db.Column(db.Date, nullable=False)
    report_type = db.Column(db.String(50), nullable=False)  # daily, weekly, incident, etc.
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='submitted')  # submitted, reviewed, approved
    reviewed_by = db.Column(db.Integer, ForeignKey('users.id'))
    reviewed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    employee = relationship("User", foreign_keys=[employee_id], backref="reports")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
    attachments = relationship("ReportAttachment", back_populates="report", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<EmployeeReport {self.id} - {self.title}>'


class ReportAttachment(db.Model):
    """Çalışan raporlarına ekler"""
    __tablename__ = 'report_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    report_id = db.Column(db.Integer, ForeignKey('employee_reports.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))  # image, document, etc.
    file_size = db.Column(db.Integer)  # in bytes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    report = relationship("EmployeeReport", back_populates="attachments")
    
    def __repr__(self):
        return f'<ReportAttachment {self.id} - {self.file_name}>'


# İrsaliye sistemi için eklemeler
class DeliveryAttachment(db.Model):
    """İrsaliyelere eklenen dosyalar"""
    __tablename__ = 'delivery_attachments'
    
    id = db.Column(db.Integer, primary_key=True)
    delivery_id = db.Column(db.Integer, ForeignKey('deliveries.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(50))  # image, document, etc.
    file_size = db.Column(db.Integer)  # in bytes
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    delivery = relationship("Delivery", backref="attachments")
    
    def __repr__(self):
        return f'<DeliveryAttachment {self.id} - {self.file_name}>'


# Araç modelleri kataloğu
class VehicleCatalog(db.Model):
    """Araç marka ve modelleri kataloğu"""
    __tablename__ = 'vehicle_catalog'
    
    id = db.Column(db.Integer, primary_key=True)
    brand = db.Column(db.String(100), nullable=False, default='IVECO')
    model = db.Column(db.String(100), nullable=False, unique=True)
    year = db.Column(db.Integer, nullable=False, default=datetime.utcnow().year)
    tonnage = db.Column(db.Float, nullable=True)  # Tonaj
    image_url = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<VehicleCatalog {self.brand} {self.model} {self.year}>'
