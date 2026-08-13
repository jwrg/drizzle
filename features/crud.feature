@integration @gui
Feature: CRUDding data model objects
  Create, read, update, delete for all pertinent data
  model types

  Background:
    Given we are looking at the dashboard

  Scenario Outline: Creating a board
     When we click the link to the <obj> list page
      And click the create button
      And name the <obj> as <name>
      And give it the description <desc>
      And assign it to index <index>
      And save the <obj>
     Then we should see the <obj> list page
      And the <obj> called <name>
      And that <name> has description <desc>
      And that <name> has index <index>

    Examples: Relay boards
     | obj | name | desc | index |
     | board | Board1 | The first board | 5 |
     | board | Board2 | The second board | 6 |

  Scenario Outline: Creating a relay
     When we click the link to the <obj> list page
      And click the create button
      And name the <obj> as <name>
      And give it the description <desc>
      And assign it to board <board>
      And assign it to index <index>
      And set its active flag to <active>
      And set its visibility flag to <visible>
      And give it dependencies <subdata>
      And save the <obj>
     Then we should see the <obj> list page
      And the <obj> called <name>
      And that <name> has description <desc>
      And that <name> belongs to board <board>
      And that <name> has address <index>
      And that <name> has its active flag set as <active>
      And that <name> has its visibility flag set as <visible>
      And that <name> has subdata <subdata>

    Examples: Relays
     | obj | name | desc | board | index | active | visible | subdata |
     | relay | Relay1 | The first relay | Board1 | 5 | True | True | [] |
     | relay | Relay2 | The second relay | Board2 | 6 | True | False | [{"relay":"Relay1","spin_up":1}] |
     | relay | Relay3 | The third relay | Board1 | 7 | False | True | [{"relay":"Relay1","spin_up":0},{"relay":"Relay2","spin_up":0}] |

  Scenario Outline: Creating a sequence
     When we click the link to the <obj> list page
      And click the create button
      And name the <obj> as <name>
      And give it the description <desc>
      And give it entries <subdata>
      And save the <obj>
     Then we should see the <obj> list page
      And the <obj> called <name>
      And that <name> has description <desc>
      And that <name> has subdata <subdata>

    Examples: Sequences
     | obj | name | desc | subdata |
     | sequence | Sequence1 | The first sequence | [{"relay":"Relay1","minutes":5},{"relay":"Relay2","minutes":9}] |
     | sequence | Sequence2 | The second sequence | [{"relay":"Relay2","minutes":4},{"relay":"Relay3","minutes":8}] |

  Scenario Outline: Creating a schedule
     When we click the link to the <obj> list page
      And click the create button
      And name the <obj> as <name>
      And give it the description <desc>
      And give it jobs <subdata>
      And save the <obj>
     Then we should see the <obj> list page
      And the <obj> called <name>
      And that <name> has description <desc>
      And that <name> has subdata <subdata>

    Examples: Schedules
     | obj | name | desc | subdata |
     | schedule | Schedule1 | The first schedule | [{"sequitur":"Sequence1","time":"15:00","weekdays":["Sunday"]}] |
     | schedule | Schedule2 | The second schedule | [{"sequitur":"Sequence1","time":"16:00","weekdays":["Monday","Tuesday"]},{"sequitur":"Sequence2","time":"14:30","weekdays":["Wednesday","Friday"]}] |

  Scenario Outline: Updating all data for a relay board
    When we click the link to the <obj> list page
     And click the edit link for the <obj> named <name>
     And give it the description <desc>
     And assign it to index <index>
     And save the <obj>
    Then we should see the <obj> list page
     And the <obj> called <name>
     And that <name> has description <desc>
     And that <name> has index <index>

    Examples: Relay boards
     | obj | name | desc | index |
     | board | Board1 | The penultimate board | 4 |
     | board | Board2 | The very last board | 5 |

  Scenario Outline: Updating all data for a relay
     When we click the link to the <obj> list page
      And click the edit link for the <obj> named <name>
      And give it the description <desc>
      And assign it to board <board>
      And assign it to index <index>
      And set its active flag to <active>
      And set its visibility flag to <visible>
      And give it dependencies <subdata>
      And save the <obj>
     Then we should see the <obj> list page
      And the <obj> called <name>
      And that <name> has description <desc>
      And that <name> belongs to board <board>
      And that <name> has address <index>
      And that <name> has its active flag set as <active>
      And that <name> has its visibility flag set as <visible>
      And that <name> has subdata <subdata>

    Examples: Relays
     | obj | name | desc | board | index | active | visible | subdata |
     | relay | Relay1 | The initial relay | Board2 | 7 | False | True | [] |
     | relay | Relay2 | The penultimate relay | Board1 | 6 | True | True | [{"relay":"Relay1","spin_up":2}] |
     | relay | Relay3 | The very last relay | Board2 | 6 | True | False | [{"relay":"Relay2","spin_up":3},{"relay":"Relay1","spin_up":4}] |

  Scenario Outline: Trying to make a cyclical dependency graph
     When we click the link to the <obj> list page
      And click the edit link for the <obj> named <name>
      And give it dependencies <subdata>
      And save the <obj>
     Then we should see the <obj> edit page
      And an error message about cyclic dependency graphs

    Examples: Relays
     | obj | name | subdata |
     | relay | Relay1 | [{"relay":"Relay2","spin_up":4}] |

  Scenario Outline: Trying to assign a board index twice
     When we click the link to the <obj> list page
      And click the edit link for the <obj> named <name>
      And assign it to index <index>
      And save the <obj>
     Then we should see the <obj> edit page
      And an error message about the index already being assigned

    Examples: Relays
     | obj | name | index |
     | relay | Relay1 | 6 |

  Scenario Outline: Updating all data for a sequence
     When we click the link to the <obj> list page
      And click the edit link for the <obj> named <name>
      And give it the description <desc>
      And give it entries <subdata>
      And save the <obj>
     Then we should see the <obj> list page
      And the <obj> called <name>
      And that <name> has description <desc>
      And that <name> has subdata <subdata>

    Examples: Sequences
     | obj | name | desc | subdata |
     | sequence | Sequence1 | The initial sequence | [{"relay":"Relay3","minutes":5},{"relay":"Relay2","minutes":11}] |
     | sequence | Sequence2 | The very last sequence | [{"relay":"Relay1","minutes":5},{"relay":"Relay2","minutes":18}] |

  Scenario Outline: Updating all data for a schedule
     When we click the link to the <obj> list page
      And click the edit link for the <obj> named <name>
      And give it the description <desc>
      And give it jobs <subdata>
      And save the <obj>
     Then we should see the <obj> list page
      And the <obj> called <name>
      And that <name> has description <desc>
      And that <name> has subdata <subdata>

    Examples: Schedules
     | obj | name | desc | subdata |
     | schedule | Schedule1 | The initial schedule | [{"sequitur":"Sequence2","time":"14:00","weekdays":["Sunday"]}] |
     | schedule | Schedule2 | The very last schedule | [{"sequitur":"Sequence2","time":"16:00","weekdays":["Tuesday", "Wednesday", "Thursday"]},{"sequitur":"Sequence1","time":"15:45","weekdays":["Wednesday","Saturday","Sunday"]}] |

  Scenario Outline: Trying to make a schedule with concurrent jobs
     When we click the link to the <obj> list page
      And click the edit link for the <obj> named <name>
      And give it the description <desc>
      And give it jobs <subdata>
      And save the <obj>
     Then we should see the <obj> edit page
      And an error message about concurrently scheduled jobs

    Examples: Schedules
     | obj | name | subdata |
     | schedule | Schedule2 | [{"sequitur":"Sequence2","time":"14:00","weekdays":["Tuesday", "Wednesday", "Thursday"]},{"sequitur":"Sequence1","time":"14:00","weekdays":["Wednesday","Saturday","Sunday"]}] |

  Scenario Outline: Trying to make a schedule with no weekdays
     When we click the link to the <obj> list page
      And click the edit link for the <obj> named <name>
      And give it the description <desc>
      And give it jobs <subdata>
      And save the <obj>
     Then we should see the <obj> edit page
      And an error message about a lack of associated weekdays

    Examples: Schedules
     | obj | name | subdata |
     | schedule | Schedule2 | [{"sequitur":"Sequence2","time":"14:00","weekdays":[]}] |

  Scenario Outline: Deleting a data model object
    When we click the link to the <obj> list page
     And click the delete link for the <obj> named <name>
     And accept the alert window
    Then we should see the <obj> list page
     But we shouldn't see the <obj> named <name>

   Examples: Schedules
    | obj | name |
    | schedule | Schedule1 |
    | schedule | Schedule2 |

   Examples: Sequences
    | obj | name |
    | sequence | Sequence1 |
    | sequence | Sequence2 |

   Examples: Relays
    | obj | name |
    | relay | Relay1 |
    | relay | Relay2 |

    Examples: Relay boards
     | obj | name |
     | board | Board1 |
     | board | Board2 |
