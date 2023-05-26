"""
Helper class for manipulating scheduling data
"""
from __future__ import annotations

from collections import deque
from datetime import date, datetime, time, timedelta

from flask import current_app

from util.jsonny import Jsonny
from util.sequencer import Sequencer
from util.timmy import Timmy


class Schedule:
    """
    Class that schedules jobs
    """

    logger = current_app.logger

    def __init__(
        self, id_number: int, name: str, jobs: dict[int, int, int, int]
    ) -> None:
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
        self.timer.set(self.jobs[0].remaining(), self.next, [])
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
                ]
            )
        )

    def __del__(self) -> None:
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

    def cleanup(self) -> None:
        """
        Destroy object contents in preparation for object deletion
        """
        self.timer.clear()
        del self.timer
        for job in self.jobs:
            del job
        self.jobs = []
        Schedule.logger.debug(
            " ".join(
                [
                    "Schedule",
                    self.name,
                    "with id number",
                    self.id_number,
                    "cleaned up",
                ]
            )
        )

    def next(self) -> None:
        """
        Run the next job
        """
        Sequencer.init_sequence(self.jobs[0].sequence)
        Schedule.logger.info(
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
        Schedule.logger.info(
            " ".join(
                [
                    "Next job is for sequence",
                    str(self.jobs[0].sequence),
                    "and runs in",
                    str(self.jobs[0].remaining()),
                ]
            )
        )
        self.timer.set(self.jobs[0].remaining(), self.next, [])

    class Job:
        """
        Helper class that wraps weekly time info and compares on next run time
        """

        def __init__(self, sequence: int, weekday: int, hour: int, minute: int) -> None:
            self.sequence = sequence
            self.weekday = weekday
            self.hour = hour
            self.minute = minute

        def __eq__(self, obj: Job) -> bool:
            return self.upcoming() == obj.upcoming()

        def __ne__(self, obj: Job) -> bool:
            return self.upcoming() != obj.upcoming()

        def __lt__(self, obj: Job) -> bool:
            return self.upcoming() < obj.upcoming()

        def __le__(self, obj: Job) -> bool:
            return self.upcoming() <= obj.upcoming()

        def __gt__(self, obj: Job) -> bool:
            return self.upcoming() > obj.upcoming()

        def __ge__(self, obj: Job) -> bool:
            return self.upcoming() >= obj.upcoming()

        def remaining(self) -> timedelta:
            """
            Return timedelta between now and the next run of this job
            """
            return self.upcoming() - datetime.now()

        def upcoming(self) -> datetime:
            """
            Return datetime when the next time this job will run
            """
            today = datetime.combine(date.today(), time())
            thisweek = today + timedelta(
                days=self.weekday - (today.isoweekday() % 7),
                hours=self.hour,
                minutes=self.minute,
            )
            return (
                thisweek if thisweek > datetime.now() else thisweek + timedelta(days=7)
            )


class Scheduler:
    """
    Static class for manipulating and keeping track of schedule objects
    """

    logger = current_app.logger

    def __init__(self) -> None:
        self.json = Jsonny.get("schedules")
        self.schedules = self.load(self.json.items())

    def load(
        self, schedule_list: dict[bool, str, str, str, str, dict]
    ) -> list[Schedule]:
        """
        Return a list of Schedule objects initialized using config data
        """
        return list(
            Schedule(schedule_id, entry["name"], entry["jobs"])
            for schedule_id, entry in schedule_list
            if entry["active"] is True
        )

    def reload(self) -> None:
        """
        Re-initialize all schedules
        """
        Scheduler.logger.info("Reloading all schedules")
        for schedule in self.schedules:
            schedule.cleanup()
            del schedule
        self.json = Jsonny.get("schedules")
        self.schedules = self.load(self.json.items())

    def activate(self, schedule_id: int) -> None:
        """
        Sets a schedule to active and persists the change
        """
        self.json[str(schedule_id)]["active"] = True
        Jsonny.put("schedules", self.json)
        self.reload()
        Scheduler.logger.info(
            " ".join(
                [
                    "Schedule",
                    self.json[str(schedule_id)]["name"],
                    "with id number",
                    str(schedule_id),
                    "set as active.",
                ]
            )
        )

    def deactivate(self, schedule_id: int) -> None:
        """
        Sets a schedule to not active and persists the change
        """
        self.json[str(schedule_id)]["active"] = False
        Jsonny.put("schedules", self.json)
        self.reload()
        Scheduler.logger.info(
            " ".join(
                [
                    "Schedule",
                    self.json[str(schedule_id)]["name"],
                    "with id number",
                    str(schedule_id),
                    "set as inactive.",
                ]
            )
        )
