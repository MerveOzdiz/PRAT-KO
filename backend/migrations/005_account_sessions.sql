CREATE TABLE account_session (
    token_hash TEXT PRIMARY KEY NOT NULL,
    account_id INTEGER NOT NULL REFERENCES user_account(id) ON DELETE CASCADE,
    expires_at INTEGER NOT NULL
);

CREATE INDEX account_session_expiry ON account_session(expires_at);
