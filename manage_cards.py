#!/usr/bin/python3
"""Manage cards and inspect the sync queue on the device.

Run on the Pi from the repo root (the DB is owned by root, like the service):

    sudo python3 manage_cards.py list
    sudo python3 manage_cards.py status
    sudo python3 manage_cards.py add --name "Person3 (Sam)" --like <existing-tag> --tap
    sudo python3 manage_cards.py add --name N --tag T --project P --task K --workspace W --user U
    sudo python3 manage_cards.py remove <tag>
    sudo python3 manage_cards.py import      # copy cards from Supabase
    sudo python3 manage_cards.py push        # push queued entries now

`--tap` reads the card from the RFID reader, which the service holds open:
stop it first (sudo systemctl stop attl) and start it again afterwards.
"""
import argparse
import sys

from Modules.wiring import build


def read_tag_from_reader():
    import serial
    print("Tap the card on the reader...")
    ser = serial.Serial('/dev/ttyS0', 9600)
    try:
        return ser.read(12).decode('utf-8').strip()
    finally:
        ser.close()


def cmd_list(app, args):
    cards = app.db.all_cards()
    if not cards:
        print("No cards.")
    for c in cards:
        state = 'IN ' if app.is_clocked_in(c['tag_uuid']) else '   '
        mirror = '' if c['supabase_synced'] else '  (not yet in Supabase)'
        print("%s %-14s %-24s project=%s task=%s%s" % (
            state, c['tag_uuid'], c['name'], c['project_id'], c['task_id'], mirror))


def cmd_status(app, args):
    active = app.db.active_entries()
    pending = app.db.pending_clockify()
    mirror = app.db.pending_supabase_entries()
    print("Cards: %d   Clocked in: %d" % (len(app.db.all_cards()), len(active)))
    for e in active:
        print("  IN  %s since %s" % (e['name'], e['start_time']))
    print("Waiting for Clockify: %d" % len(pending))
    for e in pending:
        err = ('  last error: %s' % e['last_error']) if e['last_error'] else ''
        print("  #%d %s %s -> %s (%s, %d attempts)%s" % (
            e['id'], e['name'], e['start_time'], e['end_time'] or 'running',
            e['status'], e['attempts'], err))
    print("Waiting for Supabase: %d entries, %d cards" % (len(mirror), len(app.db.unsynced_cards())))


def cmd_add(app, args):
    tag = read_tag_from_reader() if args.tap else args.tag
    if not tag:
        sys.exit("Give --tag or --tap")
    base = {}
    if args.like:
        base = app.db.get_card(args.like)
        if not base:
            sys.exit("No card with tag %s to copy from" % args.like)
    card = {
        'tag_uuid': tag,
        'name': args.name,
        'user_id': args.user or base.get('user_id'),
        'project_id': args.project or base.get('project_id'),
        'workspace_id': args.workspace or base.get('workspace_id'),
        'task_id': args.task or base.get('task_id'),
    }
    missing = [k for k, v in card.items() if not v]
    if missing:
        sys.exit("Missing: %s (pass them, or --like an existing card)" % ', '.join(missing))
    app.db.upsert_card(card)
    print("Saved %s -> %s" % (tag, args.name))
    app.syncer.push_supabase()


def cmd_remove(app, args):
    if not app.db.remove_card(args.tag):
        sys.exit("No card with tag %s" % args.tag)
    print("Removed %s" % args.tag)
    if app.syncer.mirror:
        try:
            app.syncer.mirror.delete_card(args.tag.strip())
        except Exception as e:
            print("Could not remove it from Supabase (do it in the dashboard): %s" % e)


def cmd_import(app, args):
    print("Imported %d card(s) from Supabase" % app.syncer.import_cards())


def cmd_push(app, args):
    pending = app.syncer.run()
    print("Still waiting for Clockify: %d" % pending)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest='command')
    sub.add_parser('list')
    sub.add_parser('status')
    add = sub.add_parser('add')
    add.add_argument('--name', required=True)
    add.add_argument('--tag')
    add.add_argument('--tap', action='store_true', help='read the tag from the reader')
    add.add_argument('--like', help='copy Clockify ids from this existing card')
    add.add_argument('--project')
    add.add_argument('--task')
    add.add_argument('--workspace')
    add.add_argument('--user')
    remove = sub.add_parser('remove')
    remove.add_argument('tag')
    sub.add_parser('import')
    sub.add_parser('push')
    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return
    app = build()
    {'list': cmd_list, 'status': cmd_status, 'add': cmd_add, 'remove': cmd_remove,
     'import': cmd_import, 'push': cmd_push}[args.command](app, args)


if __name__ == '__main__':
    main()
