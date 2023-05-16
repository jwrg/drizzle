from threading import Timer
from time import time as now

from flask import current_app


class Timmy:
    """
    Helper class that wraps a threading timer using minutes as its unit of
    time
    """

    logger = current_app.logger

    def __init__(self, name):
        self.name = name
        self.timer = None
        # Start time in seconds from the epoch
        self.start = 0
        # Interval time in minutes
        self.interval = 0

    def remaining(self):
        """
        Returns remaining timer interval in minutes
        """
        if self.timer is not None:
            return ((self.start + (self.interval * 60)) - now()) / 60
        return 0

    # Methods for setting and clearing timers
    def set(self, interval, callback, args):
        """
        Sets the timer 

        :param interval: specify when to call callback
        :param callback: a method to call once the interval has elapsed
        :param args: arguments for callback
        """
        if interval > self.remaining():
            if self.timer is not None:
                self.timer.cancel()
                self.timer = None
                Timmy.logger.debug(" ".join(["Timer", str(self.name), "extended."]))
            self.interval = interval
            self.start = now()
            self.timer = Timer(60.0 * interval, callback, args)
            self.timer.start()
            Timmy.logger.debug(
                " ".join(
                    [
                        "Timer",
                        str(self.name),
                        "set for",
                        str(interval),
                        "minute." if interval == 1 else "minutes.",
                    ]
                )
            )
        else:
            Timmy.logger.debug(
                " ".join(
                    [
                        "Timer",
                        str(self.name),
                        "not set! Arg",
                        str(interval),
                        "ends before currently set timer",
                    ]
                )
            )

    def clear(self):
        """
        Clears the timer
        """
        if self.timer is not None:
            self.interval = 0
            self.start = 0
            self.timer.cancel()
            self.timer = None
            Timmy.logger.debug(" ".join(["Timer", str(self.name), "cleared."]))
