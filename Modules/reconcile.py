"""Pure reconciliation logic between Clockify (source of truth) and local state.

No hardware, config, or network imports — kept pure so it is unit-testable in
isolation. The caller fetches the inputs (Supabase projects, Clockify
in-progress entries, current local sessions) and applies the returned actions.
"""


def reconcile_sessions(projects, in_progress_entries, active_sessions):
    """Compute how to bring local sessions in line with Clockify.

    Args:
        projects: list of Supabase project rows. Each maps a tag to a person:
            {tag_uuid, name, user_id, project_id, workspace_id, task_id}.
        in_progress_entries: list of Clockify in-progress time entries (the
            shape Clockify returns: id, projectId, taskId, workspaceId,
            description, billable, timeInterval.start).
        active_sessions: current local sessions keyed by tag_uuid.

    Returns:
        (to_add, to_remove)
        to_add: {tag_uuid: (user_data, entry)} sessions to create — Clockify
            entries that have no matching local session (e.g. lost to a crash,
            or a timer that was running across a restart).
        to_remove: [tag_uuid] sessions to drop — local sessions whose Clockify
            entry is no longer in progress (ended elsewhere).
    """
    by_project = {}
    for p in projects:
        # First project row wins if a project_id somehow repeats.
        by_project.setdefault(p['project_id'], p)

    live_entry_ids = set()
    to_add = {}

    for e in in_progress_entries:
        live_entry_ids.add(e['id'])
        proj = by_project.get(e.get('projectId'))
        if not proj:
            # Running entry we can't map back to a tag; leave it alone.
            continue
        tag = proj['tag_uuid']
        if tag in active_sessions:
            continue  # already tracked locally

        user_data = {
            'name': proj['name'],
            'user_id': proj['user_id'],
            'project_id': proj['project_id'],
            'workspace_id': proj['workspace_id'],
            'task_id': proj['task_id'],
        }
        entry = {
            'clockify_entry_id': e['id'],
            'workspace_id': e.get('workspaceId') or proj['workspace_id'],
            'projectId': e.get('projectId'),
            'taskId': e.get('taskId'),
            'description': e.get('description'),
            'start': e['timeInterval']['start'],
            'billable': e.get('billable', True),
        }
        to_add[tag] = (user_data, entry)

    to_remove = [
        tag
        for tag, session in active_sessions.items()
        if (session.get('entry') or {}).get('clockify_entry_id') not in live_entry_ids
    ]

    return to_add, to_remove
