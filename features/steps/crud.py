from json import loads
from hamcrest import (
    assert_that,
    empty,
    equal_to,
    instance_of,
    is_not,
    starts_with,
)
from behave import given, when, then
from util.filters import (
    filter_capitalize_first as capitalize,
    filter_pluralize as pluralize,
)

@given("we are looking at the dashboard")
def step_impl(context):
    context.browser.visit(context.dashboard_url)

@when("we click the link to the {obj} list page")
def step_impl(context, obj):
    context.browser.links.find_by_text(
        capitalize(
            pluralize(
              obj
            )
        )
    ).click()

@when("click the create button")
def step_impl(context):
    context.browser.find_by_name("new").first.click()
    
@when("name the {obj} as {name}")
def step_impl(context, obj, name):
    assert_that(context.browser.title, starts_with("Edit"))
    context.browser.fill("name", name)

@when("give it the description {desc}")
def step_impl(context, desc):
    context.browser.fill("description", desc)

@when("assign it to address {index}")
@when("assign it to index {index}")
def step_impl(context, index):
    context.browser.select("index", int(index))

@when("assign it to board {board}")
def step_impl(context, board):
    context.browser.select("board",
        context.browser.find_by_name(
            "board"
        ).find_by_text(board).value
    )

@when("set its active flag to {active}")
def step_impl(context, active):
    if active:
        context.browser.check("active")
    else:
        context.browser.uncheck("active")

@when("set its visibility flag to {visible}")
def step_impl(context, visible):
    if visible:
        context.browser.check("visible")
    else:
        context.browser.uncheck("visible")

def subdata_element(context, obj, index, name):
    return context.browser.find_by_name(
        '-'.join(
            [
                obj,
                str(index),
                name,
            ]
        )
    ).first

@when("purge extant subdata")
def step_impl(context):
    for button in reversed(context.browser.find_by_name("delete")):
        button.click()
        context.browser.get_alert().accept()

@when("give it dependencies {subdata}")
def step_impl(context, subdata):
    context.execute_steps("When purge extant subdata")
    for index, datum in enumerate(loads(subdata)):
        if index > 0:
            context.browser.find_by_name("append").first.click()
        el_select = subdata_element(
            context,
            "dependencies",
            index,
            "relay",
        )
        el_number = subdata_element(
            context,
            "dependencies",
            index,
            "spin_up",
        )
        context.browser.select(
            el_select["name"], el_select.find_by_text(
                datum["relay"]
            ).value
        )
        context.browser.fill(
            el_number["name"], datum["spin_up"]
        )

@when("give it entries {subdata}")
def step_impl(context, subdata):
    context.execute_steps("When purge extant subdata")
    for index, datum in enumerate(loads(subdata)):
        if index > 0:
            context.browser.find_by_name("append").first.click()
        el_select = subdata_element(
            context,
            "sequencia",
            index,
            "relay"
        )
        el_number = subdata_element(
            context,
            "sequencia",
            index,
            "minutes",
        )
        context.browser.select(
            el_select["name"], el_select.find_by_text(
                datum["relay"]
            ).value
        )
        context.browser.fill(
            el_number["name"], datum["minutes"]
        )

@when("give it jobs {subdata}")
def step_impl(context, subdata):
    context.execute_steps("When purge extant subdata")
    for index, datum in enumerate(loads(subdata)):
        if index > 0:
            context.browser.find_by_name("append").first.click()
        el_select = subdata_element(
            context,
            "jobs",
            index,
            "sequitur"
        )
        el_time = subdata_element(
            context,
            "jobs",
            index,
            "time",
        )
        el_multiple = subdata_element(
            context,
            "jobs",
            index,
            "weekdays"
        )
        context.browser.select(
            el_select["name"], el_select.find_by_text(
                datum["sequitur"]
            ).value
        )
        context.browser.fill(
            el_time["name"], datum["time"]
        )
        for weekday in datum["weekdays"]:
            context.browser.select(
                el_multiple["name"], el_multiple.find_by_text(
                    weekday
                ).value
            )

@when("save the {obj}")
def step_impl(context, obj):
    context.browser.find_by_name("submit").first.click()

@when("click the edit link for the {obj} named {name}")
def step_impl(context, obj, name):
    context.browser.find_by_xpath(
        "//li[starts-with(text(), '" + name + "')]/.."
    ).first.find_by_text("Edit").first.click()

@when("click the delete link for the {obj} named {name}")
def step_impl(context, obj, name):
    context.browser.find_by_xpath(
        "//li[starts-with(text(), '" + name + "')]/.."
    ).first.find_by_text("Delete").first.click()
    
@when("accept the alert window")
def step_impl(context):
    context.browser.get_alert().accept()

@then("we should see the {obj} list page")
def step_impl(context, obj):
    assert_that(context.browser.is_text_present("Create a new " + obj))
    # assert_that(context.browser.find_by_css(".current").first.text, equal_to(capitalize(pluralize(obj))))
    # assert_that(context.browser.title, equal_to(capitalize(obj) + " List - Drizzle"))

@then("we should see the {obj} edit page")
def step_impl(context, obj):
    assert_that(context.browser.is_text_present("Edit " + obj))

@then("an error message about cyclic dependency graphs")
def step_impl(context):
    assert_that(context.browser.is_text_present("Cyclic dependency graph"))

@then("an error message about concurrently scheduled jobs")
def step_impl(context):
    assert_that(context.browser.is_text_present("concurrent scheduled jobs"))

@then("we shouldn't see the {obj} named {name}")
def step_impl(context, obj, name):
    assert_that(context.browser.is_text_present("deleted"))
    assert_that(context.browser.is_element_not_present_by_xpath(
        "//li[contains(@class,'name')][contains(text(),'" + name + "')]"
    ))

@then("the {obj} called {name}")
def step_impl(context, obj, name):
    assert_that(context.browser.is_text_present("Updated"))
    assert_that(context.browser.is_element_present_by_xpath(
        "//li[contains(@class,'name')][contains(text(),'" + name + "')]"
    ))

@then("that {name} has description {desc}")
def step_impl(context, name, desc):
    assert_that(context.browser.is_text_present(desc))

@then("that {name} has address {index}")
def step_impl(context, name, index):
    assert_that(context.browser.find_by_xpath(
        "//li[starts-with(text(), '" + name + "')]/.."
    ).first.find_by_xpath(
        "li[starts-with(text(), 'Address')]"
    ).text.split()[1], equal_to(str(index)))

@then("that {name} has index {index}")
def step_impl(context, name, index):
    assert_that(context.browser.find_by_xpath(
        "//li[starts-with(text(), '" + name + "')]/.."
    ).first.find_by_xpath(
        "li[starts-with(text(), 'Index')]"
    ).text.split()[1], equal_to(str(index)))

@then("that {name} belongs to board {board}")
def step_impl(context, name, board):
    assert_that(' '.join(context.browser.find_by_xpath(
        "//li[starts-with(text(), '" + name + "')]/.."
    ).first.find_by_xpath(
        "li[starts-with(text(), 'Board')]"
    ).text.split()[1:]), equal_to(board))

@then("that {name} has its active flag set as {active}")
def step_impl(context, name, active):
    if active:
        assert_that(context.browser.find_by_xpath(
            "//li[starts-with(text(), '" + name + "')]/.."
        ).first.find_by_xpath(
            "nav/a[starts-with(text(), 'Deactivate')]"
        ), is_not(empty()))
    else:
        assert_that(context.browser.find_by_xpath(
            "//li[starts-with(text(), '" + name + "')]/.."
        ).first.find_by_xpath(
            "nav/a[starts-with(text(), 'Activate')]"
        ), is_not(empty()))
        
@then("that {name} has its visibility flag set as {visible}")
def step_impl(context, name, visible):
    if visible:
        assert_that(context.browser.find_by_xpath(
            "//li[starts-with(text(), '" + name + "')]/.."
        ).first.find_by_xpath(
            "li[starts-with(text(), 'Visible')]"
        ).text.split()[1], equal_to("Yes"))
    else:
        assert_that(context.browser.find_by_xpath(
            "//li[starts-with(text(), '" + name + "')]/.."
        ).first.find_by_xpath(
            "li[starts-with(text(), 'Visible')]"
        ).text.split()[1], equal_to("No"))

@then("that {name} has subdata {subdata}")
def step_impl(context, name, subdata):
    data = loads(subdata)
    assert_that(data, instance_of(list))
    if data != []:
        el_tbody = context.browser.find_by_xpath(
            "//li[starts-with(text(), '" + name + "')]/.."
        ).first.find_by_tag("tbody").find_by_tag("tr")
        for index, datum in enumerate(data):
            assert_that(index, instance_of(int))
            assert_that(datum, instance_of(dict))
            for key, subdatum in datum.items():
                if type(subdatum) is not list:
                    assert_that(el_tbody[index + 1].find_by_xpath(
                        "td[contains(text(), '" + str(subdatum) + "')]"
                    ), is_not(empty()))
                else:
                    for subsubdatum in subdatum:
                        assert_that(el_tbody[index + 1].find_by_xpath(
                            "td[contains(text(), '" + str(subsubdatum) + "')]"
                        ), is_not(empty()))
