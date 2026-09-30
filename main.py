#!/usr/bin/python3
import logging
import os
from logging.handlers import RotatingFileHandler
from time import sleep

from config import ROOT_DIR, STATE_FILE, SYNC_INTERVAL
from Modules.time_checker import TimeChecker
from Modules.wiring import build
import Modules.display as display


def setup_logging():
    # Rotate the log so it can't grow without bound (1 MB x 3 backups).
    handler = RotatingFileHandler(
        os.path.join(ROOT_DIR, 'attendance.log'), maxBytes=1_000_000, backupCount=3)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    # Also to stderr, which systemd sends to the journal.
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
    root.addHandler(console)


def show_idle(app):
    count = app.active_count()
    if count:
        display.displayActive(count)
    else:
        display.waitingToRead()


if __name__ == "__main__":
    setup_logging()
    display.welcomeUser()
    sleep(0.5)

    app = build()
    imported = app.import_legacy_state(STATE_FILE)
    if imported:
        logging.info("Imported %d session(s) from state.json", imported)
    if not app.db.all_cards():
        logging.info("No local cards; imported %d from Supabase", app.syncer.import_cards())

    # Overtime, sync queue, reconcile: now and every SYNC_INTERVAL seconds.
    time_checker = TimeChecker(app.tick, check_interval=SYNC_INTERVAL)
    time_checker.start()

    try:
        while True:
            try:
                show_idle(app)
                data = display.read_rfid.read_rfid()
                if not data or not data.strip():
                    continue

                result, name = app.tap(data)
                if result == 'unknown':
                    display.createRejectSound()
                    sleep(1)
                    continue

                display.createSound()
                if result == 'in':
                    display.displayRead(name)
                else:
                    display.displayEnd()
                sleep(2)  # show the message briefly

            except KeyboardInterrupt:
                raise
            except Exception as e:
                # A garbled serial read or transient error must not kill the device.
                logging.error("Loop iteration failed: %s", e)
                sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        time_checker.stop()
