"""Relational model. Documents and evidence are unique records referenced by FK."""
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import Column, String, Integer, Float, Boolean, Date, DateTime, Text, ForeignKey, UniqueConstraint, CheckConstraint, JSON, Index
from .db import Base


def uid():
    return str(uuid4())


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def fk(table, nullable=True):
    return Column(String(36), ForeignKey(f'{table}.id', ondelete='RESTRICT'), nullable=nullable, index=True)


class Record:
    id = Column(String(36), primary_key=True, default=uid)
    created_at = Column(DateTime, nullable=False, default=now)
    updated_at = Column(DateTime, nullable=False, default=now, onupdate=now)
    modified_by = fk('users')
    revision = Column(Integer, nullable=False, default=1)


class User(Record, Base):
    __tablename__ = 'users'
    name = Column(String(160), nullable=False)
    email = Column(String(254), nullable=False, unique=True)
    password_hash = Column(Text, nullable=False)
    active = Column(Boolean, nullable=False, default=True)
    department = Column(String(160), nullable=False, default='OGC')


class Role(Record, Base):
    __tablename__ = 'roles'
    name = Column(String(60), unique=True, nullable=False)


class Permission(Record, Base):
    __tablename__ = 'permissions'
    name = Column(String(80), unique=True, nullable=False)


class UserRole(Record, Base):
    __tablename__ = 'user_roles'
    user_id = fk('users', False)
    role_id = fk('roles', False)
    __table_args__ = (UniqueConstraint('user_id', 'role_id'),)


class RolePermission(Record, Base):
    __tablename__ = 'role_permissions'
    role_id = fk('roles', False)
    permission_id = fk('permissions', False)
    __table_args__ = (UniqueConstraint('role_id', 'permission_id'),)


class LoginSession(Base):
    __tablename__ = 'sessions'
    id = Column(String(64), primary_key=True)
    user_id = fk('users', False)
    csrf_hash = Column(String(64), nullable=False)
    expires_at = Column(DateTime, nullable=False)


class LoginAttempt(Base):
    __tablename__ = 'login_attempts'
    id = Column(String(64), primary_key=True)
    failures = Column(Integer, nullable=False, default=0)
    window_start = Column(DateTime, nullable=False, default=now)


class Axis(Record, Base):
    __tablename__ = 'axes'
    name = Column(String(160), nullable=False, unique=True)
    color = Column(String(16), nullable=False, default='#18847c')


class Process(Record, Base):
    __tablename__ = 'processes'
    name = Column(String(160), nullable=False, unique=True)
    axis_id = fk('axes', False)


class Project(Record, Base):
    __tablename__ = 'projects'
    title = Column(String(250), nullable=False)
    description = Column(Text, default='')
    group_key = Column(String(80), unique=True)
    axis_id = fk('axes', False)
    process_id = fk('processes')
    responsible_id = fk('users', False)
    start_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    status = Column(String(40), nullable=False, default='en_progreso')
    __table_args__ = (UniqueConstraint('axis_id', 'title', 'start_date'), CheckConstraint('due_date >= start_date', name='project_dates'),)


class Milestone(Record, Base):
    __tablename__ = 'milestones'
    title = Column(String(250), nullable=False)
    project_id = fk('projects', False)
    due_date = Column(Date, nullable=False)
    status = Column(String(40), nullable=False, default='pendiente')


class Task(Record, Base):
    __tablename__ = 'tasks'
    title = Column(String(250), nullable=False)
    description = Column(Text, default='')
    office = Column(String(160))
    project_id = fk('projects', False)
    parent_id = fk('tasks')
    responsible_id = fk('users', False)
    created_by = fk('users')
    start_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False, index=True)
    status = Column(String(40), nullable=False, default='pendiente', index=True)
    priority = Column(String(20), nullable=False, default='media')
    progress = Column(Integer, nullable=False, default=0)
    recurrence = Column(String(30), nullable=False, default='ninguna')
    recurrence_source_id = fk('tasks')
    __table_args__ = (CheckConstraint('progress >= 0 AND progress <= 100', name='task_progress'),
                      CheckConstraint('due_date >= start_date', name='task_dates'),
                      CheckConstraint("status IN ('pendiente','en_progreso','en_revision','cerrada')", name='task_status'),
                      UniqueConstraint('recurrence_source_id', 'start_date'), UniqueConstraint('project_id', 'title', 'start_date', 'responsible_id'))


class TaskAssignment(Record, Base):
    __tablename__ = 'task_assignments'
    task_id = fk('tasks', False)
    user_id = fk('users', False)
    assigned_by = fk('users')
    __table_args__ = (UniqueConstraint('task_id', 'user_id'),)


class TaskDependency(Record, Base):
    __tablename__ = 'task_dependencies'
    task_id = fk('tasks', False)
    depends_on_id = fk('tasks', False)
    __table_args__ = (UniqueConstraint('task_id', 'depends_on_id'), CheckConstraint('task_id <> depends_on_id', name='dependency_self'))


class TaskUpdate(Record, Base):
    __tablename__ = 'task_updates'
    task_id = fk('tasks', False)
    author_id = fk('users', False)
    evidence_version_id = fk('evidence_versions')
    progress = Column(Integer, nullable=False)
    comment = Column(Text, nullable=False)
    kind = Column(String(30), nullable=False, default='avance')
    __table_args__ = (CheckConstraint('progress >= 0 AND progress <= 100', name='update_progress'),)


class TaskUpdateReview(Record, Base):
    __tablename__ = 'task_update_reviews'
    task_update_id = fk('task_updates', False)
    reviewer_id = fk('users', False)
    status = Column(String(30), nullable=False)
    note = Column(Text, nullable=False)
    __table_args__ = (CheckConstraint("status IN ('validada','observada')", name='task_review_status'),
                      UniqueConstraint('task_update_id'),)


class DocumentType(Record, Base):
    __tablename__ = 'document_types'
    name = Column(String(120), nullable=False, unique=True)


class DocumentSequence(Base):
    __tablename__ = 'document_sequences'
    series = Column(String(40), primary_key=True)
    year = Column(Integer, primary_key=True)
    last_number = Column(Integer, nullable=False, default=0)
    __table_args__ = (CheckConstraint('last_number >= 0', name='document_sequence_nonnegative'),)


class Document(Record, Base):
    __tablename__ = 'documents'
    title = Column(String(250), nullable=False)
    number = Column(String(80), nullable=False)
    year = Column(Integer, nullable=False, index=True)
    document_type_id = fk('document_types', False)
    section = Column(String(30), nullable=False)
    date = Column(Date, nullable=False)
    sender = Column(String(160), nullable=False)
    recipient = Column(String(160), nullable=False)
    responsible_id = fk('users', False)
    axis_id = fk('axes')
    project_id = fk('projects')
    reference_id = fk('documents')
    preparation_status = Column(String(30), nullable=False, default='por_inicio')
    approval_status = Column(String(30), nullable=False, default='pendiente')
    sent_date = Column(Date)
    due_date = Column(Date)
    intake_format = Column(String(30))
    notebook_number = Column(String(80))
    reference_text = Column(Text)
    priority = Column(String(30))
    followup_frequency = Column(String(30))
    receipt_number = Column(String(120))
    comments = Column(Text)
    email_url = Column(Text)
    attended = Column(Boolean, nullable=False, default=False)
    drafting_assistant_id = fk('users')
    __table_args__ = (UniqueConstraint('number', 'year', 'document_type_id', 'sender'),
                      CheckConstraint("section IN ('emitidos','recibidos','normativos','archivo')", name='document_section'))


class DocumentVersion(Record, Base):
    __tablename__ = 'document_versions'
    document_id = fk('documents', False)
    version = Column(Integer, nullable=False)
    url = Column(Text, nullable=False)
    access_confirmed = Column(Boolean, nullable=False, default=False)
    author_id = fk('users', False)
    __table_args__ = (UniqueConstraint('document_id', 'version'),)


class TaskDocument(Record, Base):
    __tablename__ = 'task_documents'
    task_id = fk('tasks', False)
    document_id = fk('documents', False)
    __table_args__ = (UniqueConstraint('task_id', 'document_id'),)


class Case(Record, Base):
    __tablename__ = 'cases'
    title = Column(String(250), nullable=False)
    number = Column(String(80), nullable=False, unique=True)
    document_id = fk('documents', False)
    responsible_id = fk('users', False)
    current_department = Column(String(160), nullable=False)
    status = Column(String(30), nullable=False, default='elaboracion')
    due_date = Column(Date, nullable=False)


class CaseEvent(Record, Base):
    __tablename__ = 'case_events'
    case_id = fk('cases', False)
    actor_id = fk('users', False)
    status = Column(String(30), nullable=False)
    department = Column(String(160), nullable=False)
    note = Column(Text, nullable=False)
    resolution_id = fk('documents')


class Meeting(Record, Base):
    __tablename__ = 'meetings'
    title = Column(String(250), nullable=False)
    date = Column(DateTime, nullable=False)
    agenda = Column(Text, nullable=False)
    location = Column(String(160), nullable=False)
    responsible_id = fk('users', False)
    project_id = fk('projects')
    minutes_document_id = fk('documents')
    status = Column(String(30), nullable=False, default='programada')


class Attendee(Record, Base):
    __tablename__ = 'attendees'
    meeting_id = fk('meetings', False)
    user_id = fk('users', False)
    attended = Column(Boolean, nullable=False, default=False)
    __table_args__ = (UniqueConstraint('meeting_id', 'user_id'),)


class Agreement(Record, Base):
    __tablename__ = 'agreements'
    title = Column(String(250), nullable=False)
    meeting_id = fk('meetings', False)
    project_id = fk('projects', False)
    responsible_id = fk('users', False)
    due_date = Column(Date, nullable=False)
    task_id = fk('tasks')
    status = Column(String(30), nullable=False, default='pendiente')
    __table_args__ = (UniqueConstraint('task_id'), UniqueConstraint('meeting_id', 'title', 'responsible_id', 'due_date'))


class Evidence(Record, Base):
    __tablename__ = 'evidence'
    title = Column(String(250), nullable=False)
    category = Column(String(80), nullable=False)
    date = Column(Date, nullable=False)
    author_id = fk('users', False)
    requested_department = Column(String(160))
    due_date = Column(Date)
    request_status = Column(String(30), nullable=False, default='recibida')
    __table_args__ = (UniqueConstraint('title', 'date', 'author_id'),)


class EvidenceVersion(Record, Base):
    __tablename__ = 'evidence_versions'
    evidence_id = fk('evidence', False)
    version = Column(Integer, nullable=False)
    url = Column(Text, nullable=False)
    access_confirmed = Column(Boolean, nullable=False, default=False)
    author_id = fk('users', False)
    __table_args__ = (UniqueConstraint('evidence_id', 'version'),)


class EvidenceValidation(Record, Base):
    __tablename__ = 'evidence_validations'
    evidence_version_id = fk('evidence_versions', False)
    validator_id = fk('users', False)
    status = Column(String(30), nullable=False)
    note = Column(Text, nullable=False)
    __table_args__ = (CheckConstraint("status IN ('validada','observada')", name='evidence_validation_status'),)


class EvidenceFile(Record, Base):
    __tablename__ = 'evidence_files'
    evidence_version_id = fk('evidence_versions', False)
    storage_key = Column(String(64), nullable=False, unique=True)
    file_name = Column(String(250), nullable=False)
    content_type = Column(String(120), nullable=False)
    byte_size = Column(Integer, nullable=False)
    sha256 = Column(String(64), nullable=False)
    source_provider = Column(String(20))
    source_item_id = Column(String(256))
    source_url = Column(Text)
    __table_args__ = (UniqueConstraint('evidence_version_id'),
                      CheckConstraint('byte_size > 0', name='evidence_file_size'))


class CloudAccount(Record, Base):
    __tablename__ = 'cloud_accounts'
    user_id = fk('users', False)
    provider = Column(String(20), nullable=False)
    subject = Column(String(256), nullable=False)
    account_label = Column(String(254), nullable=False)
    token_ciphertext = Column(Text, nullable=False)
    __table_args__ = (UniqueConstraint('user_id', 'provider'),
                      CheckConstraint("provider IN ('google','microsoft')", name='cloud_provider'))


class CloudOAuthState(Base):
    __tablename__ = 'cloud_oauth_states'
    state_hash = Column(String(64), primary_key=True)
    user_id = fk('users', False)
    provider = Column(String(20), nullable=False)
    session_hash = Column(String(64), nullable=False)
    verifier_ciphertext = Column(Text, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class EvidenceLink(Record, Base):
    __tablename__ = 'evidence_links'
    evidence_id = fk('evidence', False)
    task_id = fk('tasks')
    document_id = fk('documents')
    agreement_id = fk('agreements')
    meeting_id = fk('meetings')
    project_id = fk('projects')
    indicator_id = fk('indicators')
    __table_args__ = (CheckConstraint('(CASE WHEN task_id IS NOT NULL THEN 1 ELSE 0 END + CASE WHEN document_id IS NOT NULL THEN 1 ELSE 0 END + CASE WHEN agreement_id IS NOT NULL THEN 1 ELSE 0 END + CASE WHEN meeting_id IS NOT NULL THEN 1 ELSE 0 END + CASE WHEN project_id IS NOT NULL THEN 1 ELSE 0 END + CASE WHEN indicator_id IS NOT NULL THEN 1 ELSE 0 END) = 1', name='evidence_one_target'),
                      UniqueConstraint('evidence_id', 'task_id'), UniqueConstraint('evidence_id', 'document_id'),
                      UniqueConstraint('evidence_id', 'agreement_id'), UniqueConstraint('evidence_id', 'meeting_id'),
                      UniqueConstraint('evidence_id', 'project_id'), UniqueConstraint('evidence_id', 'indicator_id'))


class ClosureApproval(Record, Base):
    __tablename__ = 'closure_approvals'
    task_id = fk('tasks', False)
    approver_id = fk('users', False)
    evidence_version_id = fk('evidence_versions')
    justification = Column(Text)
    __table_args__ = (UniqueConstraint('task_id'), CheckConstraint('evidence_version_id IS NOT NULL OR justification IS NOT NULL', name='closure_basis'),)


class ServiceOrder(Record, Base):
    __tablename__ = 'service_orders'
    title = Column(String(250), nullable=False)
    number = Column(String(80), nullable=False, unique=True)
    siaf = Column(String(80))
    provider = Column(String(160), nullable=False)
    responsible_id = fk('users', False)
    project_id = fk('projects')
    start_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    status = Column(String(30), nullable=False, default='vigente')
    __table_args__ = (CheckConstraint('due_date >= start_date', name='service_order_dates'),)


class Deliverable(Record, Base):
    __tablename__ = 'deliverables'
    title = Column(String(250), nullable=False)
    service_order_id = fk('service_orders', False)
    responsible_id = fk('users', False)
    due_date = Column(Date, nullable=False)
    presentation_document_id = fk('documents')
    status = Column(String(30), nullable=False, default='pendiente')


class DeliverableReview(Record, Base):
    __tablename__ = 'deliverable_reviews'
    deliverable_id = fk('deliverables', False)
    reviewer_id = fk('users', False)
    status = Column(String(30), nullable=False)
    note = Column(Text, nullable=False)


class QualityModel(Record, Base):
    __tablename__ = 'quality_models'
    title = Column(String(160), unique=True, nullable=False)
    version = Column(String(80), nullable=False)
    status = Column(String(30), nullable=False, default='pendiente_validacion')
    validated_by = fk('users')
    source_url = Column(Text)


class Criterion(Record, Base):
    __tablename__ = 'criteria'
    title = Column(String(250), nullable=False)
    code = Column(String(80), nullable=False)
    quality_model_id = fk('quality_models', False)
    status = Column(String(30), nullable=False, default='pendiente_validacion')
    __table_args__ = (UniqueConstraint('code', 'quality_model_id'),)


class Period(Record, Base):
    __tablename__ = 'periods'
    name = Column(String(80), unique=True, nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    __table_args__ = (CheckConstraint('end_date >= start_date', name='period_dates'),)


class Indicator(Record, Base):
    __tablename__ = 'indicators'
    title = Column(String(250), nullable=False)
    criterion_id = fk('criteria', False)
    responsible_id = fk('users', False)
    project_id = fk('projects')
    unit = Column(String(30), nullable=False, default='%')
    description = Column(Text, default='')


class IndicatorResult(Record, Base):
    __tablename__ = 'indicator_results'
    indicator_id = fk('indicators', False)
    period_id = fk('periods', False)
    target = Column(Float, nullable=False)
    result = Column(Float, nullable=False)
    __table_args__ = (UniqueConstraint('indicator_id', 'period_id'), CheckConstraint('target >= 0 AND result >= 0', name='indicator_positive'),)


class ImprovementPlan(Record, Base):
    __tablename__ = 'improvement_plans'
    title = Column(String(250), nullable=False)
    indicator_id = fk('indicators', False)
    task_id = fk('tasks')
    responsible_id = fk('users', False)
    due_date = Column(Date, nullable=False)
    status = Column(String(30), nullable=False, default='pendiente')


class CloudConfiguration(Record, Base):
    __tablename__ = 'cloud_configuration'
    settings_ciphertext = Column(Text, nullable=False)
    __table_args__ = (CheckConstraint("id = 'application'", name='cloud_configuration_singleton'),)


class Audit(Base):
    __tablename__ = 'audit'
    id = Column(String(36), primary_key=True, default=uid)
    created_at = Column(DateTime, nullable=False, default=now, index=True)
    actor_id = fk('users')
    entity = Column(String(80), nullable=False)
    record_id = Column(String(36), nullable=False)
    action = Column(String(60), nullable=False)
    before = Column(JSON)
    after = Column(JSON)


class ImportBatch(Record, Base):
    __tablename__ = 'import_batches'
    filename = Column(String(250), nullable=False)
    sha256 = Column(String(64), nullable=False)
    sheet = Column(String(160), nullable=False)
    backup_path = Column(Text, nullable=False)
    entity = Column(String(60), nullable=False)
    status = Column(String(30), nullable=False, default='preview')
    mapping = Column(JSON, nullable=False)
    preview = Column(JSON, nullable=False)
    __table_args__ = (UniqueConstraint('sha256', 'entity', 'sheet'),)


class ImportSource(Record, Base):
    __tablename__ = 'import_sources'
    batch_id = fk('import_batches', False)
    sheet = Column(String(160), nullable=False)
    row_number = Column(Integer, nullable=False)
    entity = Column(String(60), nullable=False)
    record_id = Column(String(36), nullable=False)
    __table_args__ = (UniqueConstraint('batch_id', 'sheet', 'row_number'),)
