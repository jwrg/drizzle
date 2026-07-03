from behave import given, when, then
from util.filters import (
    filter_capitalize_first as capitalize_first,
    filter_capitalize_all as capitalize_all,
    filter_pluralize as pluralize,
    filter_simple_past as simple_past,
)


@given("a phrase {input} in any mixed letter case,")
@given("a regular noun {input} singular in grammatical number,")
@given("a regular verb {input} in the present grammatical tense,")
def step_impl(context, input):
    context.input = input
    assert context.input is not None
    assert type(context.input) is str


@given("an empty string,")
def step_impl(context):
    context.input = ''
    assert type(context.input) is str


@when("fed into the capitalize_first filter")
def step_impl(context):
    context.output = capitalize_first(context.input)


@when("fed into the capitalize_all filter")
def step_impl(context):
    context.output = capitalize_all(context.input)


@when("fed into the pluralization filter")
def step_impl(context):
    context.output = pluralize(context.input)


@when("fed into the simple_past filter")
def step_impl(context):
    context.output = simple_past(context.input)


@then("it should capitalize only the first letter of the first word, as {output}.")
@then("it should capitalize the first letter of every word, as {output}.")
@then("it should come out plural in grammatical number, as {output}.")
@then("it should come out in the simple past tense, as {output}.")
def step_impl(context, output):
    assert type(output) is str
    assert type(context.output) is str
    assert context.output == output


@then("it should come out an empty string.")
def step_impl(context):
    assert type(context.output) is str
    assert context.output == ''
