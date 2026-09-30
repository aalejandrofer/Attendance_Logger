"""Pure reconciliation logic between Clockify and the local DB.

No hardware, config, or network imports, so it is unit-testable in
isolation. The caller fetches the inputs and applies the returned actions.
"""


def reconcile_sessions(cards, in_progress_entries, active_sessions, known_entry_ids=()):
    """Compute how to bring local sessions in line with Clockify.

    Args:
        cards: local card rows, each mapping a tag to a person:
            {tag_uuid, name, user_id, project_id, workspace_id, task_id}.
        in_progress_entries: Clockify in-progress time entries (id,
            projectId, taskId, workspaceId, description, billable,
            timeInterval.start).
        active_sessions: {tag_uuid: {clockify_entry_id, clockify_synced}}
            for local entries that are still active.
        known_entry_ids: every Clockify id already in the local DB. A
            running Clockify entry in this set was ended locally and is
            waiting to be pushed, so it must not be recovered.

    Returns:
        (to_add, to_remove)
        to_add: {tag_uuid: (card, clockify_entry)} running Clockify entries
            with no local session (lost to a crash, or started elsewhere).
        to_remove: [tag_uuid] synced local sessions whose Clockify entry is
            no longer running (ended elsewhere). Sessions with unpushed
            changes are left alone: Clockify can't know about them yet.
    """
    by_project = {}
    for c in cards:
        # First card wins if a project_id somehow repeats.
        by_project.setdefault(c['project_id'], c)

    known = set(known_entry_ids)
    live_entry_ids = set()
    to_add = {}

    for e in in_progress_entries:
        live_entry_ids.add(e['id'])
        if e['id'] in known:
            continue
        card = by_project.get(e.get('projectId'))
        if not card or card['tag_uuid'] in active_sessions:
            continue
        to_add[card['tag_uuid']] = (card, e)

    to_remove = [
        tag
        for tag, s in active_sessions.items()
        if s.get('clockify_synced') and s.get('clockify_entry_id')
        and s['clockify_entry_id'] not in live_entry_ids
    ]

    return to_add, to_remove
