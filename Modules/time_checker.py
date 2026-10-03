import logging
import threading
from typing import Callable, Optional


class TimeChecker:
    """Runs `task` now and then every `check_interval` seconds in a daemon thread.

    Errors are logged and never stop the loop.
    """

    def __init__(self, task: Callable[[], None], check_interval: int = 300):
        self.task = task
        self.check_interval = check_interval
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        logging.info("Time checker started")

    def stop(self):
        if self._thread:
            self._stop_event.set()
            self._thread.join()
            logging.info("Time checker stopped")

    def _run(self):
        while not self._stop_event.is_set():
            try:
                self.task()
            except Exception as e:
                logging.error("Error in time checker: %s", e)
            self._stop_event.wait(self.check_interval)
