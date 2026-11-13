CREATE TABLE catalog_product (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    brand TEXT NOT NULL,
    quantity TEXT NOT NULL,
    unit TEXT NOT NULL CHECK (unit IN ('g', 'ml', 'adet')),
    category_id INTEGER NOT NULL REFERENCES category(id),
    name_key TEXT NOT NULL,
    brand_key TEXT NOT NULL,
    UNIQUE (name_key, brand_key, quantity, unit)
);

CREATE TABLE import_batch (
    id INTEGER PRIMARY KEY,
    branch_id INTEGER NOT NULL REFERENCES branch(id),
    submitted_by INTEGER NOT NULL REFERENCES user_account(id),
    file_digest TEXT NOT NULL,
    accepted_rows INTEGER NOT NULL CHECK (accepted_rows > 0),
    rejected_rows INTEGER NOT NULL CHECK (rejected_rows >= 0),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (branch_id, file_digest),
    UNIQUE (id, branch_id)
);

CREATE TABLE price_submission (
    id INTEGER PRIMARY KEY,
    catalog_product_id INTEGER NOT NULL REFERENCES catalog_product(id),
    branch_id INTEGER NOT NULL REFERENCES branch(id),
    submitted_by INTEGER NOT NULL REFERENCES user_account(id),
    import_batch_id INTEGER,
    price_minor INTEGER NOT NULL CHECK (price_minor > 0),
    currency TEXT NOT NULL CHECK (currency IN ('TRY', 'EUR', 'USD')),
    price_scope TEXT NOT NULL CHECK (price_scope IN ('BRANCH', 'ONLINE', 'CAMPAIGN')),
    valid_until TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING' CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (import_batch_id, branch_id) REFERENCES import_batch(id, branch_id)
);

CREATE INDEX price_submission_branch_status ON price_submission(branch_id, status, id);
