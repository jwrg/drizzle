@unit @util @slow
Feature: timer class (Timmy)
  Python provides a multithreaded timer, and Timmy
  is an extension of said timer intended to be used
  as a constituent of a class that wants to time
  itself and make callbacks when the timer finishes,
  when the timer is clobbered, and when the callback
  is clobbered.

  Background:
      Given an empty timer

  Scenario: Basic timer usage
       When setting the timer with a time and a callback
       Then the timer should call the callback when the timer expires

  Scenario: Checking a set timer's finishing time
       When setting the timer with a time and a callback
        And checking the timer's finishing time
       Then the timer should return the time that was set
        And the timer should call the callback when the timer expires

  Scenario: Checking an unset timer's finishing time
       When checking the timer's finishing time
       Then the timer should return an empty datetime object

  Scenario: Checking a set timer's remaining time
       When setting the timer with a time and a callback
        And checking the timer's remaining time
       Then the timer should return the correct remaining time
        And the timer should call the callback when the timer expires

  Scenario: Checking an unset timer's remaining time
       When checking the timer's remaining time
       Then the timer should return an empty timedelta object

  Scenario: Checking whether a set timer is set
       When setting the timer with a time and a callback
        And checking whether the timer is set
       Then the timer should return true
        And the timer should call the callback when the timer expires

  Scenario: Checking whether an unset timer is set
       When checking whether the timer is set
       Then the timer should return false

  Scenario: Clearing a set timer
       When setting the timer with a time and a callback
        And clearing the timer
        And checking the timer's finishing time
        And checking the timer's remaining time
        And checking whether the timer is set
       Then the timer should return an empty datetime object
        And the timer should return an empty timedelta object
        And the timer should return false

  Scenario: Timer clobbering
       When setting the timer with a time and a callback
        And setting the timer again with a new time
       Then the timer should call the callback when the timer expires

  Scenario: Callback clobbering
       When setting the timer with a time and a callback
        And setting the timer again with a new time and a new callback
       Then the timer should call the clobbered callback
        And the timer should call the new callback when the timer expires
