"""
Helper class for manipulating scheduling data
"""
from collections import deque
from datetime import date, datetime, time, timedelta
from time import time as now

from flask import current_app

from util.jsonny import Jsonny
from util.sequencer import Sequencer
from util.timmy import Timmy


class Schedule:
    """
    Class that schedules jobs
    """

    logger = current_app.logger

    def __init__(self, id_number, name, jobs):
        self.id_number = id_number
        self.name = name
        self.jobs = deque(
            sorted(
                self.Job(
                    entry["sequence"], entry["weekday"], entry["hour"], entry["minute"]
                )
                for schedule_id, entry in jobs.items()
            )
        )
        self.timer = Timmy(name)
        self.timer.set(self.jobs[0].remaining() / 60, self.next, [])
        Schedule.logger.debug(
            " ".join(
                [
                    "Schedule",
                    self.name,
                    "with id number",
                    self.id_number,
                    "initialized containing",
                    str(len(self.jobs)),
                    "jobs.  Next job runs in",
                    str(self.jobs[0].remaining()),
                    "seconds.",
                ]
            )
        )

    def __del__(self):
        self.timer.clear()
        del self.timer
        Schedule.logger.debug(
            " ".join(
                [
                    "Schedule",
                    self.name,
                    "with id number",
                    self.id_number,
                    "terminated.",
                ]
            )
        )

    def next(self):
        """
        Run the next job
        """
        Sequencer.init_sequence(self.jobs[0].sequence)
        Schedule.logger.debug(
            " ".join(
                [
                    "Schedule",
                    str(self.name),
                    "with id number",
                    str(self.id_number),
                    "running job for sequence",
                    str(self.jobs[0].sequence),
                ]
            )
        )
        self.jobs.rotate(-1)
        Schedule.logger.debug(
            " ".join(
                [
                    "Next job is for sequence",
                    str(self.jobs[0].sequence),
                    "and runs in",
                    str(self.jobs[0].remaining()),
                    "seconds.",
                ]
            )
        )
        self.timer.set(self.jobs[0].remaining() / 60, self.next, [])

    class Job:
        """
        Helper class that wraps weekly time info and compares on next run time
        """

        def __init__(self, sequence, weekday, hour, minute):
            self.sequence = int(sequence)
            self.weekday = int(weekday)
            self.hour = int(hour)
            self.minute = int(minute)

        def __eq__(self, obj):
            return self.upcoming() == obj.upcoming()

        def __ne__(self, obj):
            return self.upcoming() != obj.upcoming()

        def __lt__(self, obj):
            return self.upcoming() < obj.upcoming()

        def __le__(self, obj):
            return self.upcoming() <= obj.upcoming()

        def __gt__(self, obj):
            return self.upcoming() > obj.upcoming()

        def __ge__(self, obj):
            return self.upcoming() >= obj.upcoming()

        def remaining(self):
            """
            Return the # of seconds between now and the next run of this job
            """
            return self.upcoming() - now()

        def upcoming(self):
            """
            Return the # of seconds from the epoch when the next time this
            job will run
            """
            today = datetime.combine(date.today(), time())
            thisweek = (
                today
                + timedelta(
                    days=self.weekday - (today.isoweekday() % 7),
                    hours=self.hour,
                    minutes=self.minute,
                )
            ).timestamp()
            return thisweek if thisweek > now() else thisweek + (7 * 24 * 3600)


class Scheduler:
    """
    Static class for manipulating and keeping track of schedule objects
    """

    logger = current_app.logger

    schedules = {
        Schedule(schedule_id, entry["name"], entry["jobs"])
        for schedule_id, entry in Jsonny.get("schedules").items()
        if entry["active"] is True
    }

    json = Jsonny.get("schedules")

    @staticmethod
    def reload():
        """
        Re-initialize all schedules
        """
        for schedule in Scheduler.schedules:
            del schedule
        Scheduler.json = Jsonny.get("schedules")
        Scheduler.schedules = {
            Schedule(schedule_id, entry["name"], entry["jobs"])
            for schedule_id, entry in Scheduler.json.items()
            if entry["active"] is True
        }

    @staticmethod
    def activate(schedule_id):
        """
        Sets a schedule to active and persists the change
        """
        Scheduler.json[str(schedule_id)]["active"] = True
        Jsonny.put("schedules", Scheduler.json)
        Scheduler.reload()
        Scheduler.logger.debug(
            " ".join(
                [
                    "Schedule",
                    Scheduler.json[str(schedule_id)]["name"],
                    "with id number",
                    str(schedule_id),
                    "set as active.",
                ]
            )
        )

    @staticmethod
    def deactivate(schedule_id):
        """
        Sets a schedule to not active and persists the change
        """
        Scheduler.json[str(schedule_id)]["active"] = False
        Jsonny.put("schedules", Scheduler.json)
        Scheduler.reload()
        Scheduler.logger.debug(
            " ".join(
                [
                    "Schedule",
                    Scheduler.json[str(schedule_id)]["name"],
                    "with id number",
                    str(schedule_id),
                    "set as inactive.",
                ]
            )
        )
