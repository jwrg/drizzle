from behave.fixture import fixture, use_fixture
from splinter import Browser

from drizzle import app

@fixture
def drizzle_client(context, *args, **kwargs):
    assert app.testing

@fixture
def browser_firefox(context, *args, **kwargs):
    context.browser = Browser("firefox")
    context.dashboard_url = "localhost:5000"
    yield context.browser
    context.browser.quit()

def before_feature(context, feature):
    use_fixture(drizzle_client, context)

def before_tag(context, tag):
    if tag == "gui":
        use_fixture(browser_firefox, context)
