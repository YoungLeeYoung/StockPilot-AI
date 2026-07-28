# Database design

StockPilot AI uses PostgreSQL through SQLAlchemy 2.0. Application code should obtain sessions from `app.db.session.get_db_session`; schema changes should be delivered through migrations rather than runtime `create_all` calls.

## Tables

### users

Stores account identity and activation state. Password hashes are optional so external identity providers can be supported later.

### watchlists

Stores one normalized stock symbol per user. The `(user_id, symbol)` pair is unique, and deleting a user removes owned watchlist records.

### analysis_history

Stores the user prompt, symbol, execution status, model name, structured investment research report, optional Agent trace, and failure message. PostgreSQL stores report and trace values as JSONB.

### investment_journals

Stores the original decision date, action, symbol, reason, thesis, price, and planned review date. Later outcome notes and AI review JSON are stored separately so retrospective analysis cannot overwrite the original decision record.

## Ownership

Watchlists, analysis history, and investment journals reference `users.id` with `ON DELETE CASCADE`. ORM relationships also use delete-orphan ownership semantics.
