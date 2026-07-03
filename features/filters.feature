@unit @util
Feature: custom template filters
  While jinja2 provides a good smattering of functional-
  paradigm data filters for use in templates, some of the
  behaviour of those filters fall short of the needs of
  Drizzle, and custom python filters can be used anywhere,
  not just in template files.

  Scenario Outline: capitalization of only the first word in a phrase
     Given a phrase <input> in any mixed letter case,
      when fed into the capitalize_first filter
      then it should capitalize only the first letter of the first word, as <output>.

    Examples: nouns
      | input | output |
      | a | A |
      | barry | Barry |
      | siphon | Siphon |
      | WORD-SALAD | WORD-SALAD |

    Examples: phrases
      | input | output |
      | barry lyndon | Barry lyndon |
      | siphon some gas, Trevor | Siphon some gas, Trevor |
      | american WORD-SALAD | American WORD-SALAD |

  Scenario Outline: capitalization of every word in a phrase
     Given a phrase <input> in any mixed letter case,
      when fed into the capitalize_all filter
      then it should capitalize the first letter of every word, as <output>.

    Examples: nouns
      | input | output |
      | a | A |
      | barry | Barry |
      | siphon | Siphon |
      | WORD-SALAD | WORD-SALAD |

    Examples: phrases
      | input | output |
      | barry lyndon | Barry Lyndon |
      | siphon some gas, Trevor | Siphon Some Gas, Trevor |
      | american WORD-SALAD | American WORD-SALAD |

  Scenario: capitalization of an empty string,
     Given an empty string,
      when fed into the capitalize_first filter
      then it should come out an empty string.

  Scenario: capitalization of an empty string,
     Given an empty string,
      when fed into the capitalize_all filter
      then it should come out an empty string.

  Scenario Outline: noun pluralization
     Given a regular noun <input> singular in grammatical number,
      when fed into the pluralization filter
      then it should come out plural in grammatical number, as <output>.

    Examples: regular nouns
      | input | output |
      | dog | dogs |
      | doggy | doggies |
      | truss | trusses |
      | hex | hexes |
      | quiz | quizzes |
      | spoke | spokes |
      | area | areas |

  Scenario Outline: verb conjugation into simple past tense
     Given a regular verb <input> in the present grammatical tense,
      when fed into the simple_past filter
      then it should come out in the simple past tense, as <output>.

    Examples: regular verbs
      | input | output |
      | activate | activated |
      | delete | deleted |
      | bark | barked |
      | vex | vexed |
      | rob | robbed |
      | clod | clodded |
      | ram | rammed |
      | bin | binned |
      | lop | lopped |
      | beg | begged |
      | bang | banged |
      | buzz | buzzed |
      | quiz | quizzed |
      | trial | trialled |
