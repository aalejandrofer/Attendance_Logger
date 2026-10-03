-- Let the device (anon key) keep the online copy up to date.
-- The device upserts cards into `projects` (on tag_uuid) and entries into
-- `time_entries` (on clockify_entry_id); upserts need INSERT and UPDATE.
-- Safe to re-run.
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE time_entries ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS device_read_projects ON projects;
DROP POLICY IF EXISTS device_insert_projects ON projects;
DROP POLICY IF EXISTS device_update_projects ON projects;
DROP POLICY IF EXISTS device_delete_projects ON projects;
CREATE POLICY device_read_projects ON projects FOR SELECT TO anon USING (true);
CREATE POLICY device_insert_projects ON projects FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY device_update_projects ON projects FOR UPDATE TO anon USING (true) WITH CHECK (true);
CREATE POLICY device_delete_projects ON projects FOR DELETE TO anon USING (true);

DROP POLICY IF EXISTS device_read_time_entries ON time_entries;
DROP POLICY IF EXISTS device_insert_time_entries ON time_entries;
DROP POLICY IF EXISTS device_update_time_entries ON time_entries;
CREATE POLICY device_read_time_entries ON time_entries FOR SELECT TO anon USING (true);
CREATE POLICY device_insert_time_entries ON time_entries FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY device_update_time_entries ON time_entries FOR UPDATE TO anon USING (true) WITH CHECK (true);
