-- LeadPilot AI LP-1 · SQLite schema

CREATE TABLE alembic_version (
	version_num VARCHAR(32) NOT NULL,
	CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

CREATE TABLE assignments (
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	lead_id VARCHAR NOT NULL,
	rep_id VARCHAR NOT NULL,
	utility FLOAT NOT NULL,
	status VARCHAR NOT NULL,
	approved_by VARCHAR NOT NULL,
	policy_version VARCHAR NOT NULL,
	created_at VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(tenant_id) REFERENCES tenants (id),
	FOREIGN KEY(lead_id) REFERENCES leads (id),
	FOREIGN KEY(rep_id) REFERENCES sales_reps (id)
);

CREATE TABLE audit_events (
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	actor VARCHAR NOT NULL,
	action VARCHAR NOT NULL,
	target_id VARCHAR NOT NULL,
	reason VARCHAR NOT NULL,
	"before" JSON NOT NULL,
	"after" JSON NOT NULL,
	created_at VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(tenant_id) REFERENCES tenants (id)
);

CREATE TABLE campaigns (
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	name VARCHAR NOT NULL,
	source VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(tenant_id) REFERENCES tenants (id)
);

CREATE TABLE communications (
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	lead_id VARCHAR NOT NULL,
	direction VARCHAR NOT NULL,
	channel VARCHAR NOT NULL,
	body VARCHAR NOT NULL,
	status VARCHAR NOT NULL,
	consent_snapshot VARCHAR NOT NULL,
	simulated BOOLEAN NOT NULL,
	created_at VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(tenant_id) REFERENCES tenants (id),
	FOREIGN KEY(lead_id) REFERENCES leads (id)
);

CREATE TABLE idempotency (
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	fingerprint VARCHAR NOT NULL,
	response JSON NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(tenant_id) REFERENCES tenants (id)
);

CREATE TABLE jobs (
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	lead_id VARCHAR NOT NULL,
	task_id VARCHAR,
	correlation_id VARCHAR NOT NULL,
	created_at VARCHAR NOT NULL,
	due_at VARCHAR NOT NULL,
	status VARCHAR NOT NULL,
	retry_count INTEGER NOT NULL,
	locked_until VARCHAR,
	last_error VARCHAR,
	payload JSON NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(tenant_id) REFERENCES tenants (id),
	FOREIGN KEY(lead_id) REFERENCES leads (id),
	FOREIGN KEY(task_id) REFERENCES tasks (id)
);

CREATE TABLE lead_events (
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	lead_id VARCHAR NOT NULL,
	kind VARCHAR NOT NULL,
	payload JSON NOT NULL,
	actor VARCHAR NOT NULL,
	origin VARCHAR NOT NULL,
	correlation_id VARCHAR NOT NULL,
	created_at VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(tenant_id) REFERENCES tenants (id),
	FOREIGN KEY(lead_id) REFERENCES leads (id)
);

CREATE TABLE leads (
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	external_id VARCHAR NOT NULL,
	name VARCHAR NOT NULL,
	contact VARCHAR NOT NULL,
	email VARCHAR NOT NULL,
	source VARCHAR NOT NULL,
	campaign_id VARCHAR,
	city VARCHAR NOT NULL,
	interest VARCHAR NOT NULL,
	inquiry VARCHAR NOT NULL,
	budget INTEGER,
	urgency VARCHAR NOT NULL,
	stage VARCHAR NOT NULL,
	owner_id VARCHAR,
	score FLOAT NOT NULL,
	consent VARCHAR NOT NULL,
	consent_source VARCHAR NOT NULL,
	consent_at VARCHAR,
	opt_out_at VARCHAR,
	created_at VARCHAR NOT NULL,
	updated_at VARCHAR NOT NULL,
	responded_at VARCHAR,
	appointment_at VARCHAR,
	outcome_verified BOOLEAN NOT NULL,
	deal_value INTEGER NOT NULL,
	deleted BOOLEAN NOT NULL,
	is_synthetic BOOLEAN NOT NULL, first_response_at VARCHAR,
	PRIMARY KEY (id),
	UNIQUE (tenant_id, external_id),
	UNIQUE (tenant_id, contact),
	FOREIGN KEY(tenant_id) REFERENCES tenants (id),
	FOREIGN KEY(campaign_id) REFERENCES campaigns (id),
	FOREIGN KEY(owner_id) REFERENCES sales_reps (id)
);

CREATE TABLE memberships (
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	user_id VARCHAR NOT NULL,
	role VARCHAR NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (tenant_id, user_id),
	FOREIGN KEY(tenant_id) REFERENCES tenants (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE recommendations (
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	lead_id VARCHAR,
	agent VARCHAR NOT NULL,
	action VARCHAR NOT NULL,
	inputs JSON NOT NULL,
	alternatives JSON NOT NULL,
	explanation JSON NOT NULL,
	status VARCHAR NOT NULL,
	policy_version VARCHAR NOT NULL,
	created_at VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(tenant_id) REFERENCES tenants (id),
	FOREIGN KEY(lead_id) REFERENCES leads (id)
);

CREATE TABLE sales_reps (
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	user_id VARCHAR NOT NULL,
	name VARCHAR NOT NULL,
	skills JSON NOT NULL,
	capacity INTEGER NOT NULL,
	active BOOLEAN NOT NULL,
	shift_start INTEGER NOT NULL,
	shift_end INTEGER NOT NULL,
	response FLOAT NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(tenant_id) REFERENCES tenants (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE sessions (
	id VARCHAR NOT NULL,
	user_id VARCHAR NOT NULL,
	csrf VARCHAR NOT NULL,
	expires VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(user_id) REFERENCES users (id)
);

CREATE TABLE tasks (
	id VARCHAR NOT NULL,
	tenant_id VARCHAR NOT NULL,
	lead_id VARCHAR NOT NULL,
	assigned_to VARCHAR,
	kind VARCHAR NOT NULL,
	due_at VARCHAR NOT NULL,
	status VARCHAR NOT NULL,
	completed_at VARCHAR,
	created_at VARCHAR NOT NULL,
	PRIMARY KEY (id),
	FOREIGN KEY(tenant_id) REFERENCES tenants (id),
	FOREIGN KEY(lead_id) REFERENCES leads (id),
	FOREIGN KEY(assigned_to) REFERENCES sales_reps (id)
);

CREATE TABLE tenants (
	id VARCHAR NOT NULL,
	name VARCHAR NOT NULL,
	settings JSON NOT NULL,
	clock VARCHAR NOT NULL,
	PRIMARY KEY (id)
);

CREATE TABLE users (
	id VARCHAR NOT NULL,
	email VARCHAR NOT NULL,
	name VARCHAR NOT NULL,
	password_hash VARCHAR NOT NULL,
	PRIMARY KEY (id),
	UNIQUE (email)
);

CREATE INDEX ix_assignments_tenant_id ON assignments (tenant_id);

CREATE INDEX ix_audit_events_tenant_id ON audit_events (tenant_id);

CREATE INDEX ix_campaigns_tenant_id ON campaigns (tenant_id);

CREATE INDEX ix_communications_tenant_id ON communications (tenant_id);

CREATE INDEX ix_idempotency_tenant_id ON idempotency (tenant_id);

CREATE INDEX ix_jobs_tenant_id ON jobs (tenant_id);

CREATE INDEX ix_lead_events_lead_id ON lead_events (lead_id);

CREATE INDEX ix_lead_events_tenant_id ON lead_events (tenant_id);

CREATE INDEX ix_leads_stage ON leads (stage);

CREATE INDEX ix_leads_tenant_id ON leads (tenant_id);

CREATE INDEX ix_memberships_tenant_id ON memberships (tenant_id);

CREATE INDEX ix_recommendations_tenant_id ON recommendations (tenant_id);

CREATE INDEX ix_sales_reps_tenant_id ON sales_reps (tenant_id);

CREATE INDEX ix_tasks_lead_id ON tasks (lead_id);

CREATE INDEX ix_tasks_tenant_id ON tasks (tenant_id);
