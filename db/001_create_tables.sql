-- Projects table that combines user and RFID information
CREATE TABLE projects (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    user_id TEXT NOT NULL,
    tag_uuid TEXT UNIQUE NOT NULL,
    task_id TEXT NOT NULL,
    project_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Time entries table for logging
CREATE TABLE time_entries (
    id uuid DEFAULT uuid_generate_v4() PRIMARY KEY,
    project_id TEXT NOT NULL,
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE,
    description TEXT,
    clockify_entry_id TEXT UNIQUE,
    status TEXT CHECK (status IN ('active', 'completed', 'limit_reached')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now())
);

-- Indexes
CREATE INDEX idx_projects_tag_uuid ON projects(tag_uuid);
CREATE INDEX idx_time_entries_status ON time_entries(status);
CREATE INDEX idx_time_entries_project_id ON time_entries(project_id);
