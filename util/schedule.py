"""
Helper class for manipulating scheduling data
"""
from __future__ import annotations

from collections import deque
from datetime import date, datetime, time, timedelta

from flask import current_app

from util.sequencer import Sequencer, Sequitur
from util.singleton import singleton
from util.persist import PersistentMapping
from util.timmy import Timmy

sequences = Sequencer()


class Job:
    """
    Helper class that wraps weekly time info and compares on next run time
    """

    def __init__(
        self,
        sequence: Sequitur,
        weekday: int,
        hour: int,
        minute: int
    ) -> None:
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
        Return datetime when the next time tmessagehis job will run
        """
        today = datetime.combine(date.today(), time())
        thisweek = today + timedelta(
            days=self.weekday - (today.isoweekday() % 7),
            hours=self.hour,
            minutes=self.minute,
        )
        return (
            thisweek if thisweek > datetime.now()
            else thisweek + timedelta(days=7)
        )


class Schedule:
    """
    Class that schedules jobs
    """

    logger = current_app.logger

    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        active: bool,
        jobs: deque[Job]
    ) -> None:
        self.id = id
        self.name = name
        self.description = description
        self.active = active
        self.jobs = jobs
        self.timer = Timmy(name)
        Schedule.logger.debug(
            " ".join(
                [
                    "Schedule",
                    self.name,
                    "with id",
                    self.id,
                    "initialized containing",
                    str(len(self.jobs)),
                    "jobs.",
                ]
            )
        )
        if self.active:
            self.on()

    def off(self) -> None:
        self.timer.clear()
        self.active = False
        Schedule.logger.debug(
            " ".join(
                [
                    "Schedule",
                    str(self.name),
                    "turned off.",
                ]
            )
        )

    def on(self) -> None:
        self.jobs = deque(sorted(self.jobs))
        self.timer.set(self.jobs[0].remaining(), self.next, [])
        self.active = True
        Schedule.logger.debug(
            " ".join(
                [
                    "Schedule",
                    str(self.name),
                    "turned on.",
                    "Next job runs in",
                    str(self.jobs[0].remaining()),
                ]
            )
        )

    def next(self) -> None:
        # """
        # Run the next job
        # """
        self.jobs[0].sequence.start()
        Schedule.logger.info(
            " ".join(
                [
                    "Schedule",
                    str(self.name),
                    "with id",
                    str(self.id),
                    "running job, sequence",
                    str(self.jobs[0].sequence.name),
                ]
            )
        )
        self.jobs.rotate(-1)
        Schedule.logger.info(
            " ".join(
                [
                    "Next job is for sequence",
                    str(self.jobs[0].sequence.name),
                    "and runs in",
                    str(self.jobs[0].remaining()),
                ]
            )
        )
        self.timer.set(self.jobs[0].remaining(), self.next, [])


@singleton
class Scheduler(PersistentMapping):
    """
    Class for keeping track of schedule objects
    """

    default_filename = "schedules"
    logger = current_app.logger

    def __init__(self, filename: str = default_filename) -> None:
        super().__init__(filename)

    def __delitem__(self, key):
        self.collection[key].timer.clear()
        del self.collection[key].timer
        for job in self.collection[key].jobs:
            del job
        self.collection[key].jobs = []
        Scheduler.logger.debug(
            " ".join(
                [
                    "Schedule",
                    self.collection[key].name,
                    "with id",
                    self.collection[key].id,
                    "deleted.",
                ]
            )
        )
        super().__delitem__(key)

    def to_obj(
        self, collection: dict[str, dict]
    ) -> dict[str, Schedule]:
        return {
            id: Schedule(
                id,
                schedule["name"],
                schedule["description"],
                schedule["active"],
                deque(
                    Job(
                        sequences[job["sequence"]],
                        job["weekday"],
                        job["hour"],
                        job["minute"]
                    )
                    for job in schedule["jobs"]
                ),
            )
            for id, schedule in collection.items()
        }

    def to_json(self, collection: dict[str, Schedule]):
        return {
            id: {
                "description": schedule.description,
                "name": schedule.name,
                "modified": datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f%Z"),
                "active": schedule.active,
                "jobs": [
                    {
                        "sequence": job.sequence.id,
                        "weekday": job.weekday,
                        "hour": job.hour,
                        "minute": job.minute
                    }
                    for job in list(schedule.jobs)
                ]
            }
            for id, schedule in collection.items()
        }
