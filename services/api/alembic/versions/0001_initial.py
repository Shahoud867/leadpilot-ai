"""Frozen initial LP-1 SQLite schema."""

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None
SCHEMA = [
    "\nCREATE TABLE tenants (\n\tid VARCHAR NOT NULL, \n\tname VARCHAR NOT NULL, \n\tsettings JSON NOT NULL, \n\tclock VARCHAR NOT NULL, \n\tPRIMARY KEY (id)\n)\n\n",
    "\nCREATE TABLE users (\n\tid VARCHAR NOT NULL, \n\temail VARCHAR NOT NULL, \n\tname VARCHAR NOT NULL, \n\tpassword_hash VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tUNIQUE (email)\n)\n\n",
    '\nCREATE TABLE audit_events (\n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tactor VARCHAR NOT NULL, \n\taction VARCHAR NOT NULL, \n\ttarget_id VARCHAR NOT NULL, \n\treason VARCHAR NOT NULL, \n\t"before" JSON NOT NULL, \n\t"after" JSON NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenants (id)\n)\n\n',
    "CREATE INDEX ix_audit_events_tenant_id ON audit_events (tenant_id)",
    "\nCREATE TABLE campaigns (\n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tname VARCHAR NOT NULL, \n\tsource VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenants (id)\n)\n\n",
    "CREATE INDEX ix_campaigns_tenant_id ON campaigns (tenant_id)",
    "\nCREATE TABLE idempotency (\n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tfingerprint VARCHAR NOT NULL, \n\tresponse JSON NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenants (id)\n)\n\n",
    "CREATE INDEX ix_idempotency_tenant_id ON idempotency (tenant_id)",
    "\nCREATE TABLE memberships (\n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tuser_id VARCHAR NOT NULL, \n\trole VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenants (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id), \n\tUNIQUE (tenant_id, user_id)\n)\n\n",
    "CREATE INDEX ix_memberships_tenant_id ON memberships (tenant_id)",
    "\nCREATE TABLE sales_reps (\n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tuser_id VARCHAR NOT NULL, \n\tname VARCHAR NOT NULL, \n\tskills JSON NOT NULL, \n\tcapacity INTEGER NOT NULL, \n\tactive BOOLEAN NOT NULL, \n\tshift_start INTEGER NOT NULL, \n\tshift_end INTEGER NOT NULL, \n\tresponse DOUBLE NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenants (id)\n)\n\n",
    "CREATE INDEX ix_sales_reps_tenant_id ON sales_reps (tenant_id)",
    "\nCREATE TABLE sessions (\n\tid VARCHAR NOT NULL, \n\tuser_id VARCHAR NOT NULL, \n\tcsrf VARCHAR NOT NULL, \n\texpires VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(user_id) REFERENCES users (id)\n)\n\n",
    "\nCREATE TABLE leads (\n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\texternal_id VARCHAR NOT NULL, \n\tname VARCHAR NOT NULL, \n\tcontact VARCHAR NOT NULL, \n\temail VARCHAR NOT NULL, \n\tsource VARCHAR NOT NULL, \n\tcampaign_id VARCHAR, \n\tcity VARCHAR NOT NULL, \n\tinterest VARCHAR NOT NULL, \n\tinquiry VARCHAR NOT NULL, \n\tbudget INTEGER, \n\turgency VARCHAR NOT NULL, \n\tstage VARCHAR NOT NULL, \n\towner_id VARCHAR, \n\tscore DOUBLE NOT NULL, \n\tconsent VARCHAR NOT NULL, \n\tconsent_source VARCHAR NOT NULL, \n\tconsent_at VARCHAR, \n\topt_out_at VARCHAR, \n\tcreated_at VARCHAR NOT NULL, \n\tupdated_at VARCHAR NOT NULL, \n\tresponded_at VARCHAR, \n\tappointment_at VARCHAR, \n\toutcome_verified BOOLEAN NOT NULL, \n\tdeal_value INTEGER NOT NULL, \n\tdeleted BOOLEAN NOT NULL, \n\tis_synthetic BOOLEAN NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(campaign_id) REFERENCES campaigns (id), \n\tUNIQUE (tenant_id, external_id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenants (id), \n\tUNIQUE (tenant_id, contact), \n\tFOREIGN KEY(owner_id) REFERENCES sales_reps (id)\n)\n\n",
    "CREATE INDEX ix_leads_stage ON leads (stage)",
    "CREATE INDEX ix_leads_tenant_id ON leads (tenant_id)",
    "\nCREATE TABLE assignments (\n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tlead_id VARCHAR NOT NULL, \n\trep_id VARCHAR NOT NULL, \n\tutility DOUBLE NOT NULL, \n\tstatus VARCHAR NOT NULL, \n\tapproved_by VARCHAR NOT NULL, \n\tpolicy_version VARCHAR NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(lead_id) REFERENCES leads (id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenants (id), \n\tFOREIGN KEY(rep_id) REFERENCES sales_reps (id)\n)\n\n",
    "CREATE INDEX ix_assignments_tenant_id ON assignments (tenant_id)",
    "\nCREATE TABLE communications (\n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tlead_id VARCHAR NOT NULL, \n\tdirection VARCHAR NOT NULL, \n\tchannel VARCHAR NOT NULL, \n\tbody VARCHAR NOT NULL, \n\tstatus VARCHAR NOT NULL, \n\tconsent_snapshot VARCHAR NOT NULL, \n\tsimulated BOOLEAN NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(lead_id) REFERENCES leads (id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenants (id)\n)\n\n",
    "CREATE INDEX ix_communications_tenant_id ON communications (tenant_id)",
    "\nCREATE TABLE lead_events (\n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tlead_id VARCHAR NOT NULL, \n\tkind VARCHAR NOT NULL, \n\tpayload JSON NOT NULL, \n\tactor VARCHAR NOT NULL, \n\torigin VARCHAR NOT NULL, \n\tcorrelation_id VARCHAR NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenants (id), \n\tFOREIGN KEY(lead_id) REFERENCES leads (id)\n)\n\n",
    "CREATE INDEX ix_lead_events_lead_id ON lead_events (lead_id)",
    "CREATE INDEX ix_lead_events_tenant_id ON lead_events (tenant_id)",
    "\nCREATE TABLE recommendations (\n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tlead_id VARCHAR, \n\tagent VARCHAR NOT NULL, \n\taction VARCHAR NOT NULL, \n\tinputs JSON NOT NULL, \n\talternatives JSON NOT NULL, \n\texplanation JSON NOT NULL, \n\tstatus VARCHAR NOT NULL, \n\tpolicy_version VARCHAR NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenants (id), \n\tFOREIGN KEY(lead_id) REFERENCES leads (id)\n)\n\n",
    "CREATE INDEX ix_recommendations_tenant_id ON recommendations (tenant_id)",
    "\nCREATE TABLE tasks (\n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tlead_id VARCHAR NOT NULL, \n\tassigned_to VARCHAR, \n\tkind VARCHAR NOT NULL, \n\tdue_at VARCHAR NOT NULL, \n\tstatus VARCHAR NOT NULL, \n\tcompleted_at VARCHAR, \n\tcreated_at VARCHAR NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(lead_id) REFERENCES leads (id), \n\tFOREIGN KEY(assigned_to) REFERENCES sales_reps (id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenants (id)\n)\n\n",
    "CREATE INDEX ix_tasks_lead_id ON tasks (lead_id)",
    "CREATE INDEX ix_tasks_tenant_id ON tasks (tenant_id)",
    "\nCREATE TABLE jobs (\n\tid VARCHAR NOT NULL, \n\ttenant_id VARCHAR NOT NULL, \n\tlead_id VARCHAR NOT NULL, \n\ttask_id VARCHAR, \n\tcorrelation_id VARCHAR NOT NULL, \n\tcreated_at VARCHAR NOT NULL, \n\tdue_at VARCHAR NOT NULL, \n\tstatus VARCHAR NOT NULL, \n\tretry_count INTEGER NOT NULL, \n\tlocked_until VARCHAR, \n\tlast_error VARCHAR, \n\tpayload JSON NOT NULL, \n\tPRIMARY KEY (id), \n\tFOREIGN KEY(tenant_id) REFERENCES tenants (id), \n\tFOREIGN KEY(task_id) REFERENCES tasks (id), \n\tFOREIGN KEY(lead_id) REFERENCES leads (id)\n)\n\n",
    "CREATE INDEX ix_jobs_tenant_id ON jobs (tenant_id)",
]


def upgrade():
    for statement in SCHEMA:
        op.execute(statement)


def downgrade():
    op.drop_table("jobs")
    op.drop_table("tasks")
    op.drop_table("recommendations")
    op.drop_table("lead_events")
    op.drop_table("communications")
    op.drop_table("assignments")
    op.drop_table("leads")
    op.drop_table("sessions")
    op.drop_table("sales_reps")
    op.drop_table("memberships")
    op.drop_table("idempotency")
    op.drop_table("campaigns")
    op.drop_table("audit_events")
    op.drop_table("users")
    op.drop_table("tenants")
