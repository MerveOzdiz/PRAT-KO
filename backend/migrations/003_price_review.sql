ALTER TABLE price_submission ADD COLUMN reviewed_by INTEGER REFERENCES user_account(id);
ALTER TABLE price_submission ADD COLUMN reviewed_at TEXT;
ALTER TABLE price_submission ADD COLUMN rejection_reason TEXT;

CREATE INDEX price_submission_review_queue ON price_submission(status, id);
CREATE INDEX price_submission_offer_history
    ON price_submission(branch_id, catalog_product_id, price_scope, currency, status, id);
