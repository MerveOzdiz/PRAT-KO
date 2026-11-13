CREATE TABLE user_account (
    id INTEGER PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'USER' CHECK (role IN ('USER', 'OWNER', 'ADMIN')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ownership_application (
    id INTEGER PRIMARY KEY,
    applicant_id INTEGER NOT NULL REFERENCES user_account(id),
    business_name TEXT NOT NULL,
    branch_name TEXT NOT NULL,
    address TEXT NOT NULL,
    latitude REAL NOT NULL CHECK (latitude BETWEEN -90 AND 90),
    longitude REAL NOT NULL CHECK (longitude BETWEEN -180 AND 180),
    google_place_id TEXT NOT NULL,
    verification_note TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    decided_by INTEGER REFERENCES user_account(id),
    decided_at TEXT,
    rejection_reason TEXT,
    branch_id INTEGER REFERENCES branch(id)
);

CREATE UNIQUE INDEX ownership_one_pending
    ON ownership_application(applicant_id, google_place_id) WHERE status = 'PENDING';

CREATE INDEX ownership_review_queue ON ownership_application(status, id);

CREATE TABLE branch_membership (
    branch_id INTEGER PRIMARY KEY REFERENCES branch(id),
    user_id INTEGER NOT NULL REFERENCES user_account(id),
    application_id INTEGER NOT NULL UNIQUE REFERENCES ownership_application(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX branch_membership_user ON branch_membership(user_id);
