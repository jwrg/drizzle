from behave import given, when, then
from datetime import datetime, timedelta
from time import sleep
from util.timmy import Timmy


class TimerTest:
    test_time = 3

    def __init__(self):
        self.flag1 = False
        self.flag2 = False

    def set_flag(self, flag: int):
        if flag == 1:
            self.flag1 = True
        elif flag == 2:
            self.flag2 = True


@given("an empty timer")
def step_impl(context):
    context.timer_test = TimerTest()
    context.timer = Timmy("Testing timer")


@when("setting the timer with a time and a callback")
@when("setting the timer again with a new time")
def step_impl(context):
    context.set_time = datetime.now() + timedelta(seconds=TimerTest.test_time)
    context.timer.set(
        timedelta(seconds=TimerTest.test_time),
        context.timer_test.set_flag, [1]
    )


@when("setting the timer again with a new time and a new callback")
def step_impl(context):
    context.set_time = datetime.now() + timedelta(seconds=TimerTest.test_time)
    context.timer.set(
        timedelta(seconds=TimerTest.test_time),
        context.timer_test.set_flag, [2]
    )


@when("clearing the timer")
def step_impl(context):
    context.timer.clear()


@when("checking the timer's finishing time")
def step_impl(context):
    context.finished = context.timer.finished()


@when("checking the timer's remaining time")
def step_impl(context):
    context.remaining = context.timer.remaining()


@when("checking whether the timer is set")
def step_impl(context):
    context.is_set = context.timer.is_set()


@then("the timer should return the time that was set")
def step_impl(context):
    assert context.finished > datetime.now()
    assert context.finished < datetime.now() + timedelta(
        seconds=TimerTest.test_time
    )


@then("the timer should return the correct remaining time")
def step_impl(context):
    assert context.remaining > timedelta(seconds=0)
    assert context.remaining < timedelta(seconds=TimerTest.test_time)


@then("the timer should return true")
def step_impl(context):
    assert context.is_set is True


@then("the timer should return an empty datetime object")
def step_impl(context):
    assert context.finished == datetime.min


@then("the timer should return an empty timedelta object")
def step_impl(context):
    assert context.remaining == timedelta()


@then("the timer should return false")
def step_impl(context):
    assert context.is_set is False


@then("the timer should call the clobbered callback")
def step_impl(context):
    assert context.timer_test.flag1 is True


@then("the timer should call the callback when the timer expires")
def step_impl(context):
    assert context.timer_test.flag1 is False
    sleep(TimerTest.test_time)
    assert context.timer_test.flag1 is True


@then("the timer should call the new callback when the timer expires")
def step_impl(context):
    assert context.timer_test.flag2 is False
    sleep(TimerTest.test_time)
    assert context.timer_test.flag2 is True
