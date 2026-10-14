-- ROADMAP OGC · esquema inicial congelado
-- Aplicar mediante alembic upgrade head.

CREATE SCHEMA IF NOT EXISTS roadmap;

CREATE TABLE roadmap.users (
	name VARCHAR(160) NOT NULL, 
	email VARCHAR(254) NOT NULL, 
	password_hash TEXT NOT NULL, 
	active BOOLEAN NOT NULL, 
	department VARCHAR(160) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (email), 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_users_modified_by ON roadmap.users (modified_by);

CREATE TABLE roadmap.login_attempts (
	id VARCHAR(64) NOT NULL, 
	failures INTEGER NOT NULL, 
	window_start TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id)
);

CREATE TABLE roadmap.roles (
	name VARCHAR(60) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_roles_modified_by ON roadmap.roles (modified_by);

CREATE TABLE roadmap.permissions (
	name VARCHAR(80) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_permissions_modified_by ON roadmap.permissions (modified_by);

CREATE TABLE roadmap.sessions (
	id VARCHAR(64) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	csrf_hash VARCHAR(64) NOT NULL, 
	expires_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(user_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_sessions_user_id ON roadmap.sessions (user_id);

CREATE TABLE roadmap.axes (
	name VARCHAR(160) NOT NULL, 
	color VARCHAR(16) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_axes_modified_by ON roadmap.axes (modified_by);

CREATE TABLE roadmap.document_types (
	name VARCHAR(120) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_document_types_modified_by ON roadmap.document_types (modified_by);

CREATE TABLE roadmap.evidence (
	title VARCHAR(250) NOT NULL, 
	category VARCHAR(80) NOT NULL, 
	date DATE NOT NULL, 
	author_id VARCHAR(36) NOT NULL, 
	requested_department VARCHAR(160), 
	due_date DATE, 
	request_status VARCHAR(30) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (title, date, author_id), 
	FOREIGN KEY(author_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_evidence_modified_by ON roadmap.evidence (modified_by);

CREATE INDEX ix_evidence_author_id ON roadmap.evidence (author_id);

CREATE TABLE roadmap.quality_models (
	title VARCHAR(160) NOT NULL, 
	version VARCHAR(80) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	validated_by VARCHAR(36), 
	source_url TEXT, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (title), 
	FOREIGN KEY(validated_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_quality_models_modified_by ON roadmap.quality_models (modified_by);

CREATE INDEX ix_quality_models_validated_by ON roadmap.quality_models (validated_by);

CREATE TABLE roadmap.periods (
	name VARCHAR(80) NOT NULL, 
	start_date DATE NOT NULL, 
	end_date DATE NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT period_dates CHECK (end_date >= start_date), 
	UNIQUE (name), 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_periods_modified_by ON roadmap.periods (modified_by);

CREATE TABLE roadmap.audit (
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	actor_id VARCHAR(36), 
	entity VARCHAR(80) NOT NULL, 
	record_id VARCHAR(36) NOT NULL, 
	action VARCHAR(60) NOT NULL, 
	before JSON, 
	after JSON, 
	PRIMARY KEY (id), 
	FOREIGN KEY(actor_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_audit_created_at ON roadmap.audit (created_at);

CREATE INDEX ix_audit_actor_id ON roadmap.audit (actor_id);

CREATE TABLE roadmap.import_batches (
	filename VARCHAR(250) NOT NULL, 
	sha256 VARCHAR(64) NOT NULL, 
	sheet VARCHAR(160) NOT NULL, 
	backup_path TEXT NOT NULL, 
	entity VARCHAR(60) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	mapping JSON NOT NULL, 
	preview JSON NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (sha256, entity, sheet), 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_import_batches_modified_by ON roadmap.import_batches (modified_by);

CREATE TABLE roadmap.user_roles (
	user_id VARCHAR(36) NOT NULL, 
	role_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (user_id, role_id), 
	FOREIGN KEY(user_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(role_id) REFERENCES roadmap.roles (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_user_roles_modified_by ON roadmap.user_roles (modified_by);

CREATE INDEX ix_user_roles_role_id ON roadmap.user_roles (role_id);

CREATE INDEX ix_user_roles_user_id ON roadmap.user_roles (user_id);

CREATE TABLE roadmap.role_permissions (
	role_id VARCHAR(36) NOT NULL, 
	permission_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (role_id, permission_id), 
	FOREIGN KEY(role_id) REFERENCES roadmap.roles (id) ON DELETE RESTRICT, 
	FOREIGN KEY(permission_id) REFERENCES roadmap.permissions (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_role_permissions_permission_id ON roadmap.role_permissions (permission_id);

CREATE INDEX ix_role_permissions_modified_by ON roadmap.role_permissions (modified_by);

CREATE INDEX ix_role_permissions_role_id ON roadmap.role_permissions (role_id);

CREATE TABLE roadmap.processes (
	name VARCHAR(160) NOT NULL, 
	axis_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name), 
	FOREIGN KEY(axis_id) REFERENCES roadmap.axes (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_processes_modified_by ON roadmap.processes (modified_by);

CREATE INDEX ix_processes_axis_id ON roadmap.processes (axis_id);

CREATE TABLE roadmap.evidence_versions (
	evidence_id VARCHAR(36) NOT NULL, 
	version INTEGER NOT NULL, 
	url TEXT NOT NULL, 
	access_confirmed BOOLEAN NOT NULL, 
	author_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (evidence_id, version), 
	FOREIGN KEY(evidence_id) REFERENCES roadmap.evidence (id) ON DELETE RESTRICT, 
	FOREIGN KEY(author_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_evidence_versions_modified_by ON roadmap.evidence_versions (modified_by);

CREATE INDEX ix_evidence_versions_author_id ON roadmap.evidence_versions (author_id);

CREATE INDEX ix_evidence_versions_evidence_id ON roadmap.evidence_versions (evidence_id);

CREATE TABLE roadmap.criteria (
	title VARCHAR(250) NOT NULL, 
	code VARCHAR(80) NOT NULL, 
	quality_model_id VARCHAR(36) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code, quality_model_id), 
	FOREIGN KEY(quality_model_id) REFERENCES roadmap.quality_models (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_criteria_modified_by ON roadmap.criteria (modified_by);

CREATE INDEX ix_criteria_quality_model_id ON roadmap.criteria (quality_model_id);

CREATE TABLE roadmap.import_sources (
	batch_id VARCHAR(36) NOT NULL, 
	sheet VARCHAR(160) NOT NULL, 
	row_number INTEGER NOT NULL, 
	entity VARCHAR(60) NOT NULL, 
	record_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (batch_id, sheet, row_number), 
	FOREIGN KEY(batch_id) REFERENCES roadmap.import_batches (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_import_sources_batch_id ON roadmap.import_sources (batch_id);

CREATE INDEX ix_import_sources_modified_by ON roadmap.import_sources (modified_by);

CREATE TABLE roadmap.projects (
	title VARCHAR(250) NOT NULL, 
	description TEXT, 
	axis_id VARCHAR(36) NOT NULL, 
	process_id VARCHAR(36), 
	responsible_id VARCHAR(36) NOT NULL, 
	start_date DATE NOT NULL, 
	due_date DATE NOT NULL, 
	status VARCHAR(40) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (axis_id, title, start_date), 
	CONSTRAINT project_dates CHECK (due_date >= start_date), 
	FOREIGN KEY(axis_id) REFERENCES roadmap.axes (id) ON DELETE RESTRICT, 
	FOREIGN KEY(process_id) REFERENCES roadmap.processes (id) ON DELETE RESTRICT, 
	FOREIGN KEY(responsible_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_projects_responsible_id ON roadmap.projects (responsible_id);

CREATE INDEX ix_projects_modified_by ON roadmap.projects (modified_by);

CREATE INDEX ix_projects_process_id ON roadmap.projects (process_id);

CREATE INDEX ix_projects_due_date ON roadmap.projects (due_date);

CREATE INDEX ix_projects_axis_id ON roadmap.projects (axis_id);

CREATE TABLE roadmap.evidence_validations (
	evidence_version_id VARCHAR(36) NOT NULL, 
	validator_id VARCHAR(36) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	note TEXT NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT evidence_validation_status CHECK (status IN ('validada','observada')), 
	FOREIGN KEY(evidence_version_id) REFERENCES roadmap.evidence_versions (id) ON DELETE RESTRICT, 
	FOREIGN KEY(validator_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_evidence_validations_validator_id ON roadmap.evidence_validations (validator_id);

CREATE INDEX ix_evidence_validations_modified_by ON roadmap.evidence_validations (modified_by);

CREATE INDEX ix_evidence_validations_evidence_version_id ON roadmap.evidence_validations (evidence_version_id);

CREATE TABLE roadmap.milestones (
	title VARCHAR(250) NOT NULL, 
	project_id VARCHAR(36) NOT NULL, 
	due_date DATE NOT NULL, 
	status VARCHAR(40) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(project_id) REFERENCES roadmap.projects (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_milestones_project_id ON roadmap.milestones (project_id);

CREATE INDEX ix_milestones_modified_by ON roadmap.milestones (modified_by);

CREATE TABLE roadmap.tasks (
	title VARCHAR(250) NOT NULL, 
	description TEXT, 
	project_id VARCHAR(36) NOT NULL, 
	parent_id VARCHAR(36), 
	responsible_id VARCHAR(36) NOT NULL, 
	start_date DATE NOT NULL, 
	due_date DATE NOT NULL, 
	status VARCHAR(40) NOT NULL, 
	priority VARCHAR(20) NOT NULL, 
	progress INTEGER NOT NULL, 
	recurrence VARCHAR(30) NOT NULL, 
	recurrence_source_id VARCHAR(36), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT task_progress CHECK (progress >= 0 AND progress <= 100), 
	CONSTRAINT task_dates CHECK (due_date >= start_date), 
	CONSTRAINT task_status CHECK (status IN ('pendiente','en_progreso','en_revision','cerrada')), 
	UNIQUE (recurrence_source_id, start_date), 
	UNIQUE (project_id, title, start_date, responsible_id), 
	FOREIGN KEY(project_id) REFERENCES roadmap.projects (id) ON DELETE RESTRICT, 
	FOREIGN KEY(parent_id) REFERENCES roadmap.tasks (id) ON DELETE RESTRICT, 
	FOREIGN KEY(responsible_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(recurrence_source_id) REFERENCES roadmap.tasks (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_tasks_responsible_id ON roadmap.tasks (responsible_id);

CREATE INDEX ix_tasks_recurrence_source_id ON roadmap.tasks (recurrence_source_id);

CREATE INDEX ix_tasks_due_date ON roadmap.tasks (due_date);

CREATE INDEX ix_tasks_modified_by ON roadmap.tasks (modified_by);

CREATE INDEX ix_tasks_parent_id ON roadmap.tasks (parent_id);

CREATE INDEX ix_tasks_project_id ON roadmap.tasks (project_id);

CREATE INDEX ix_tasks_status ON roadmap.tasks (status);

CREATE TABLE roadmap.documents (
	title VARCHAR(250) NOT NULL, 
	number VARCHAR(80) NOT NULL, 
	year INTEGER NOT NULL, 
	document_type_id VARCHAR(36) NOT NULL, 
	section VARCHAR(30) NOT NULL, 
	date DATE NOT NULL, 
	sender VARCHAR(160) NOT NULL, 
	recipient VARCHAR(160) NOT NULL, 
	responsible_id VARCHAR(36) NOT NULL, 
	project_id VARCHAR(36), 
	reference_id VARCHAR(36), 
	preparation_status VARCHAR(30) NOT NULL, 
	approval_status VARCHAR(30) NOT NULL, 
	sent_date DATE, 
	due_date DATE, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (number, year, document_type_id, sender), 
	CONSTRAINT document_section CHECK (section IN ('emitidos','recibidos','normativos','archivo')), 
	FOREIGN KEY(document_type_id) REFERENCES roadmap.document_types (id) ON DELETE RESTRICT, 
	FOREIGN KEY(responsible_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(project_id) REFERENCES roadmap.projects (id) ON DELETE RESTRICT, 
	FOREIGN KEY(reference_id) REFERENCES roadmap.documents (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_documents_year ON roadmap.documents (year);

CREATE INDEX ix_documents_responsible_id ON roadmap.documents (responsible_id);

CREATE INDEX ix_documents_document_type_id ON roadmap.documents (document_type_id);

CREATE INDEX ix_documents_project_id ON roadmap.documents (project_id);

CREATE INDEX ix_documents_modified_by ON roadmap.documents (modified_by);

CREATE INDEX ix_documents_reference_id ON roadmap.documents (reference_id);

CREATE TABLE roadmap.service_orders (
	title VARCHAR(250) NOT NULL, 
	number VARCHAR(80) NOT NULL, 
	siaf VARCHAR(80), 
	provider VARCHAR(160) NOT NULL, 
	responsible_id VARCHAR(36) NOT NULL, 
	project_id VARCHAR(36), 
	start_date DATE NOT NULL, 
	due_date DATE NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT service_order_dates CHECK (due_date >= start_date), 
	UNIQUE (number), 
	FOREIGN KEY(responsible_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(project_id) REFERENCES roadmap.projects (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_service_orders_responsible_id ON roadmap.service_orders (responsible_id);

CREATE INDEX ix_service_orders_modified_by ON roadmap.service_orders (modified_by);

CREATE INDEX ix_service_orders_project_id ON roadmap.service_orders (project_id);

CREATE TABLE roadmap.indicators (
	title VARCHAR(250) NOT NULL, 
	criterion_id VARCHAR(36) NOT NULL, 
	responsible_id VARCHAR(36) NOT NULL, 
	project_id VARCHAR(36), 
	unit VARCHAR(30) NOT NULL, 
	description TEXT, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(criterion_id) REFERENCES roadmap.criteria (id) ON DELETE RESTRICT, 
	FOREIGN KEY(responsible_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(project_id) REFERENCES roadmap.projects (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_indicators_modified_by ON roadmap.indicators (modified_by);

CREATE INDEX ix_indicators_responsible_id ON roadmap.indicators (responsible_id);

CREATE INDEX ix_indicators_project_id ON roadmap.indicators (project_id);

CREATE INDEX ix_indicators_criterion_id ON roadmap.indicators (criterion_id);

CREATE TABLE roadmap.task_assignments (
	task_id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (task_id, user_id), 
	FOREIGN KEY(task_id) REFERENCES roadmap.tasks (id) ON DELETE RESTRICT, 
	FOREIGN KEY(user_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_task_assignments_modified_by ON roadmap.task_assignments (modified_by);

CREATE INDEX ix_task_assignments_task_id ON roadmap.task_assignments (task_id);

CREATE INDEX ix_task_assignments_user_id ON roadmap.task_assignments (user_id);

CREATE TABLE roadmap.task_dependencies (
	task_id VARCHAR(36) NOT NULL, 
	depends_on_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (task_id, depends_on_id), 
	CONSTRAINT dependency_self CHECK (task_id <> depends_on_id), 
	FOREIGN KEY(task_id) REFERENCES roadmap.tasks (id) ON DELETE RESTRICT, 
	FOREIGN KEY(depends_on_id) REFERENCES roadmap.tasks (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_task_dependencies_depends_on_id ON roadmap.task_dependencies (depends_on_id);

CREATE INDEX ix_task_dependencies_modified_by ON roadmap.task_dependencies (modified_by);

CREATE INDEX ix_task_dependencies_task_id ON roadmap.task_dependencies (task_id);

CREATE TABLE roadmap.task_updates (
	task_id VARCHAR(36) NOT NULL, 
	author_id VARCHAR(36) NOT NULL, 
	progress INTEGER NOT NULL, 
	comment TEXT NOT NULL, 
	kind VARCHAR(30) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT update_progress CHECK (progress >= 0 AND progress <= 100), 
	FOREIGN KEY(task_id) REFERENCES roadmap.tasks (id) ON DELETE RESTRICT, 
	FOREIGN KEY(author_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_task_updates_author_id ON roadmap.task_updates (author_id);

CREATE INDEX ix_task_updates_task_id ON roadmap.task_updates (task_id);

CREATE INDEX ix_task_updates_modified_by ON roadmap.task_updates (modified_by);

CREATE TABLE roadmap.document_versions (
	document_id VARCHAR(36) NOT NULL, 
	version INTEGER NOT NULL, 
	url TEXT NOT NULL, 
	access_confirmed BOOLEAN NOT NULL, 
	author_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (document_id, version), 
	FOREIGN KEY(document_id) REFERENCES roadmap.documents (id) ON DELETE RESTRICT, 
	FOREIGN KEY(author_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_document_versions_document_id ON roadmap.document_versions (document_id);

CREATE INDEX ix_document_versions_modified_by ON roadmap.document_versions (modified_by);

CREATE INDEX ix_document_versions_author_id ON roadmap.document_versions (author_id);

CREATE TABLE roadmap.task_documents (
	task_id VARCHAR(36) NOT NULL, 
	document_id VARCHAR(36) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (task_id, document_id), 
	FOREIGN KEY(task_id) REFERENCES roadmap.tasks (id) ON DELETE RESTRICT, 
	FOREIGN KEY(document_id) REFERENCES roadmap.documents (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_task_documents_modified_by ON roadmap.task_documents (modified_by);

CREATE INDEX ix_task_documents_task_id ON roadmap.task_documents (task_id);

CREATE INDEX ix_task_documents_document_id ON roadmap.task_documents (document_id);

CREATE TABLE roadmap.cases (
	title VARCHAR(250) NOT NULL, 
	number VARCHAR(80) NOT NULL, 
	document_id VARCHAR(36) NOT NULL, 
	responsible_id VARCHAR(36) NOT NULL, 
	current_department VARCHAR(160) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	due_date DATE NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (number), 
	FOREIGN KEY(document_id) REFERENCES roadmap.documents (id) ON DELETE RESTRICT, 
	FOREIGN KEY(responsible_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_cases_modified_by ON roadmap.cases (modified_by);

CREATE INDEX ix_cases_document_id ON roadmap.cases (document_id);

CREATE INDEX ix_cases_responsible_id ON roadmap.cases (responsible_id);

CREATE TABLE roadmap.meetings (
	title VARCHAR(250) NOT NULL, 
	date TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	agenda TEXT NOT NULL, 
	location VARCHAR(160) NOT NULL, 
	responsible_id VARCHAR(36) NOT NULL, 
	project_id VARCHAR(36), 
	minutes_document_id VARCHAR(36), 
	status VARCHAR(30) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(responsible_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(project_id) REFERENCES roadmap.projects (id) ON DELETE RESTRICT, 
	FOREIGN KEY(minutes_document_id) REFERENCES roadmap.documents (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_meetings_responsible_id ON roadmap.meetings (responsible_id);

CREATE INDEX ix_meetings_minutes_document_id ON roadmap.meetings (minutes_document_id);

CREATE INDEX ix_meetings_modified_by ON roadmap.meetings (modified_by);

CREATE INDEX ix_meetings_project_id ON roadmap.meetings (project_id);

CREATE TABLE roadmap.closure_approvals (
	task_id VARCHAR(36) NOT NULL, 
	approver_id VARCHAR(36) NOT NULL, 
	evidence_version_id VARCHAR(36), 
	justification TEXT, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (task_id), 
	CONSTRAINT closure_basis CHECK (evidence_version_id IS NOT NULL OR justification IS NOT NULL), 
	FOREIGN KEY(task_id) REFERENCES roadmap.tasks (id) ON DELETE RESTRICT, 
	FOREIGN KEY(approver_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(evidence_version_id) REFERENCES roadmap.evidence_versions (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_closure_approvals_modified_by ON roadmap.closure_approvals (modified_by);

CREATE INDEX ix_closure_approvals_approver_id ON roadmap.closure_approvals (approver_id);

CREATE INDEX ix_closure_approvals_evidence_version_id ON roadmap.closure_approvals (evidence_version_id);

CREATE INDEX ix_closure_approvals_task_id ON roadmap.closure_approvals (task_id);

CREATE TABLE roadmap.deliverables (
	title VARCHAR(250) NOT NULL, 
	service_order_id VARCHAR(36) NOT NULL, 
	responsible_id VARCHAR(36) NOT NULL, 
	due_date DATE NOT NULL, 
	presentation_document_id VARCHAR(36), 
	status VARCHAR(30) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(service_order_id) REFERENCES roadmap.service_orders (id) ON DELETE RESTRICT, 
	FOREIGN KEY(responsible_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(presentation_document_id) REFERENCES roadmap.documents (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_deliverables_responsible_id ON roadmap.deliverables (responsible_id);

CREATE INDEX ix_deliverables_service_order_id ON roadmap.deliverables (service_order_id);

CREATE INDEX ix_deliverables_presentation_document_id ON roadmap.deliverables (presentation_document_id);

CREATE INDEX ix_deliverables_modified_by ON roadmap.deliverables (modified_by);

CREATE TABLE roadmap.indicator_results (
	indicator_id VARCHAR(36) NOT NULL, 
	period_id VARCHAR(36) NOT NULL, 
	target FLOAT NOT NULL, 
	result FLOAT NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (indicator_id, period_id), 
	CONSTRAINT indicator_positive CHECK (target >= 0 AND result >= 0), 
	FOREIGN KEY(indicator_id) REFERENCES roadmap.indicators (id) ON DELETE RESTRICT, 
	FOREIGN KEY(period_id) REFERENCES roadmap.periods (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_indicator_results_indicator_id ON roadmap.indicator_results (indicator_id);

CREATE INDEX ix_indicator_results_modified_by ON roadmap.indicator_results (modified_by);

CREATE INDEX ix_indicator_results_period_id ON roadmap.indicator_results (period_id);

CREATE TABLE roadmap.improvement_plans (
	title VARCHAR(250) NOT NULL, 
	indicator_id VARCHAR(36) NOT NULL, 
	task_id VARCHAR(36), 
	responsible_id VARCHAR(36) NOT NULL, 
	due_date DATE NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(indicator_id) REFERENCES roadmap.indicators (id) ON DELETE RESTRICT, 
	FOREIGN KEY(task_id) REFERENCES roadmap.tasks (id) ON DELETE RESTRICT, 
	FOREIGN KEY(responsible_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_improvement_plans_responsible_id ON roadmap.improvement_plans (responsible_id);

CREATE INDEX ix_improvement_plans_task_id ON roadmap.improvement_plans (task_id);

CREATE INDEX ix_improvement_plans_modified_by ON roadmap.improvement_plans (modified_by);

CREATE INDEX ix_improvement_plans_indicator_id ON roadmap.improvement_plans (indicator_id);

CREATE TABLE roadmap.case_events (
	case_id VARCHAR(36) NOT NULL, 
	actor_id VARCHAR(36) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	department VARCHAR(160) NOT NULL, 
	note TEXT NOT NULL, 
	resolution_id VARCHAR(36), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(case_id) REFERENCES roadmap.cases (id) ON DELETE RESTRICT, 
	FOREIGN KEY(actor_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(resolution_id) REFERENCES roadmap.documents (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_case_events_resolution_id ON roadmap.case_events (resolution_id);

CREATE INDEX ix_case_events_actor_id ON roadmap.case_events (actor_id);

CREATE INDEX ix_case_events_modified_by ON roadmap.case_events (modified_by);

CREATE INDEX ix_case_events_case_id ON roadmap.case_events (case_id);

CREATE TABLE roadmap.attendees (
	meeting_id VARCHAR(36) NOT NULL, 
	user_id VARCHAR(36) NOT NULL, 
	attended BOOLEAN NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (meeting_id, user_id), 
	FOREIGN KEY(meeting_id) REFERENCES roadmap.meetings (id) ON DELETE RESTRICT, 
	FOREIGN KEY(user_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_attendees_modified_by ON roadmap.attendees (modified_by);

CREATE INDEX ix_attendees_meeting_id ON roadmap.attendees (meeting_id);

CREATE INDEX ix_attendees_user_id ON roadmap.attendees (user_id);

CREATE TABLE roadmap.agreements (
	title VARCHAR(250) NOT NULL, 
	meeting_id VARCHAR(36) NOT NULL, 
	project_id VARCHAR(36) NOT NULL, 
	responsible_id VARCHAR(36) NOT NULL, 
	due_date DATE NOT NULL, 
	task_id VARCHAR(36), 
	status VARCHAR(30) NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (task_id), 
	UNIQUE (meeting_id, title, responsible_id, due_date), 
	FOREIGN KEY(meeting_id) REFERENCES roadmap.meetings (id) ON DELETE RESTRICT, 
	FOREIGN KEY(project_id) REFERENCES roadmap.projects (id) ON DELETE RESTRICT, 
	FOREIGN KEY(responsible_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(task_id) REFERENCES roadmap.tasks (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_agreements_project_id ON roadmap.agreements (project_id);

CREATE INDEX ix_agreements_responsible_id ON roadmap.agreements (responsible_id);

CREATE INDEX ix_agreements_meeting_id ON roadmap.agreements (meeting_id);

CREATE INDEX ix_agreements_modified_by ON roadmap.agreements (modified_by);

CREATE INDEX ix_agreements_task_id ON roadmap.agreements (task_id);

CREATE TABLE roadmap.deliverable_reviews (
	deliverable_id VARCHAR(36) NOT NULL, 
	reviewer_id VARCHAR(36) NOT NULL, 
	status VARCHAR(30) NOT NULL, 
	note TEXT NOT NULL, 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(deliverable_id) REFERENCES roadmap.deliverables (id) ON DELETE RESTRICT, 
	FOREIGN KEY(reviewer_id) REFERENCES roadmap.users (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_deliverable_reviews_modified_by ON roadmap.deliverable_reviews (modified_by);

CREATE INDEX ix_deliverable_reviews_deliverable_id ON roadmap.deliverable_reviews (deliverable_id);

CREATE INDEX ix_deliverable_reviews_reviewer_id ON roadmap.deliverable_reviews (reviewer_id);

CREATE TABLE roadmap.evidence_links (
	evidence_id VARCHAR(36) NOT NULL, 
	task_id VARCHAR(36), 
	document_id VARCHAR(36), 
	agreement_id VARCHAR(36), 
	meeting_id VARCHAR(36), 
	project_id VARCHAR(36), 
	indicator_id VARCHAR(36), 
	id VARCHAR(36) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE NOT NULL, 
	modified_by VARCHAR(36), 
	revision INTEGER NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT evidence_one_target CHECK ((CASE WHEN task_id IS NOT NULL THEN 1 ELSE 0 END + CASE WHEN document_id IS NOT NULL THEN 1 ELSE 0 END + CASE WHEN agreement_id IS NOT NULL THEN 1 ELSE 0 END + CASE WHEN meeting_id IS NOT NULL THEN 1 ELSE 0 END + CASE WHEN project_id IS NOT NULL THEN 1 ELSE 0 END + CASE WHEN indicator_id IS NOT NULL THEN 1 ELSE 0 END) = 1), 
	UNIQUE (evidence_id, task_id), 
	UNIQUE (evidence_id, document_id), 
	UNIQUE (evidence_id, agreement_id), 
	UNIQUE (evidence_id, meeting_id), 
	UNIQUE (evidence_id, project_id), 
	UNIQUE (evidence_id, indicator_id), 
	FOREIGN KEY(evidence_id) REFERENCES roadmap.evidence (id) ON DELETE RESTRICT, 
	FOREIGN KEY(task_id) REFERENCES roadmap.tasks (id) ON DELETE RESTRICT, 
	FOREIGN KEY(document_id) REFERENCES roadmap.documents (id) ON DELETE RESTRICT, 
	FOREIGN KEY(agreement_id) REFERENCES roadmap.agreements (id) ON DELETE RESTRICT, 
	FOREIGN KEY(meeting_id) REFERENCES roadmap.meetings (id) ON DELETE RESTRICT, 
	FOREIGN KEY(project_id) REFERENCES roadmap.projects (id) ON DELETE RESTRICT, 
	FOREIGN KEY(indicator_id) REFERENCES roadmap.indicators (id) ON DELETE RESTRICT, 
	FOREIGN KEY(modified_by) REFERENCES roadmap.users (id) ON DELETE RESTRICT
);

CREATE INDEX ix_evidence_links_evidence_id ON roadmap.evidence_links (evidence_id);

CREATE INDEX ix_evidence_links_task_id ON roadmap.evidence_links (task_id);

CREATE INDEX ix_evidence_links_project_id ON roadmap.evidence_links (project_id);

CREATE INDEX ix_evidence_links_document_id ON roadmap.evidence_links (document_id);

CREATE INDEX ix_evidence_links_indicator_id ON roadmap.evidence_links (indicator_id);

CREATE INDEX ix_evidence_links_modified_by ON roadmap.evidence_links (modified_by);

CREATE INDEX ix_evidence_links_meeting_id ON roadmap.evidence_links (meeting_id);

CREATE INDEX ix_evidence_links_agreement_id ON roadmap.evidence_links (agreement_id);
