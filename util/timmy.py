"""
Helper class for multithreaded timing
"""
from datetime import datetime, timedelta
from threading import Timer
from typing import Any, Callable

from flask import current_app


class Timmy:
    """
    Helper class that wraps a threading timer using timedelta for intervals
    """

    logger = current_app.logger

    def __init__(self, name: str) -> None:
        self.name = name
        self.timer = None
        self.start = None
        self.interval = None
        self.callback = None
        self.args = None

    def finished(self) -> datetime:
        """
        Returns datetime indicating when the timer will be finished counting
        """
        return self.start + self.interval if self.timer is not None else datetime()

    def remaining(self) -> timedelta:
        """
        Returns remaining timer interval
        """
        return self.finished() - datetime.now() if self.timer is not None else timedelta()

    # Methods for setting and clearing timers
    def set(
        self, interval: timedelta, callback: Callable[[...], Any], args: list[str]
    ) -> None:
        """
        Sets the timer

        :param interval: specify when to call callback
        :param callback: a method to call once the interval has elapsed
        :param args: arguments for callback
        """
        if interval > self.remaining():
            if self.timer is not None:
                Timmy.logger.debug(
                    " ".join(
                        [
                            "Timer",
                            str(self.name),
                            "thread",
                            str(self.timer.native_id),
                            "has been reset before finishing!",
                        ]
                    )
                )
                if callback != self.callback or args != self.args:
                    Timmy.logger.debug(
                        " ".join(
                            [
                                "Timer",
                                str(self.name),
                                "thread",
                                str(self.timer.native_id),
                                "used to have callback",
                                str(self.callback),
                                "with args",
                                str(self.args),
                                "but has been changed to callback",
                                str(callback),
                                "with args",
                                str(args),
                            ]
                        )
                    )
                self.timer.cancel()
                del self.timer
                self.timer = None
            self.interval = interval
            self.start = datetime.now()
            self.callback = callback
            self.args = args
            self.timer = Timer(interval.total_seconds(), callback, args)
            self.timer.start()
            Timmy.logger.info(
                " ".join(
                    [
                        "Timer",
                        str(self.name),
                        "thread",
                        str(self.timer.native_id),
                        "set for",
                        str(interval),
                    ]
                )
            )
        else:
            Timmy.logger.debug(
                " ".join(
                    [
                        "Timer",
                        str(self.name),
                        "thread",
                        str(self.timer.native_id),
                        "not set! Arg",
                        str(interval),
                        "ends before currently set timer",
                    ]
                )
            )

    def clear(self) -> None:
        """
        Clears the timer
        """
        if self.timer is not None:
            self.interval = None
            self.start = None
            self.timer.cancel()
            Timmy.logger.info(
                " ".join(
                    [
                        "Timer",
                        str(self.name),
                        "thread",
                        str(self.timer.native_id),
                        "cleared.",
                    ]
                )
            )
            del self.timer
            self.timer = None
