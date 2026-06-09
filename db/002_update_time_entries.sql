ALTER TABLE time_entries 
ADD COLUMN IF NOT EXISTS clockify_entry_id TEXT,
ADD UNIQUE(clockify_entry_id);

CREATE INDEX IF NOT EXISTS idx_time_entries_clockify_id ON time_entries(clockify_entry_id);