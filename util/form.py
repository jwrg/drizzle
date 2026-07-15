from flask import current_app
from flask_wtf import FlaskForm
from wtforms import (
    Form,
    FieldList,
    FormField,
    SelectField,
    SelectMultipleField,
    BooleanField,
    IntegerField,
    HiddenField,
    RadioField,
    StringField,
    SubmitField,
    TextAreaField,
    TimeField,
    validators
)
from wtforms.widgets import html_params, HiddenInput, Select


class ButtonWidget:
    input_type = "button"

    html_params = staticmethod(html_params)

    def __call__(self, field, **kwargs):
        kwargs.setdefault("id", field.id)
        kwargs.setdefault("type", self.input_type)
        if "value" not in kwargs:
            kwargs["value"] = field._value()

        return "<button {params}>{label}</button>".format(
            params=self.html_params(name=field.name, **kwargs),
            label=field.label.text
        )


class ButtonField(StringField):
    widget = ButtonWidget()


class BasicForm(FlaskForm):
    name = StringField("Name", validators=[validators.Length(min=4, max=64)])
    description = TextAreaField(
        "Description",
        render_kw={"rows": "3"},
        validators=[validators.Length(max=255)]
    )
    submit = SubmitField()


std_length = validators.Length(min=3, max=64)


class RunningTimeForm(Form):
    time = IntegerField("Running time", validators=[
        validators.NumberRange(min=1)
    ])


class ConfigForm(FlaskForm):
    LOG_LEVEL = IntegerField("Log level", widget=HiddenInput(), validators=[
        validators.NumberRange(min=1, max=50)
    ])
    APP_PORT = IntegerField("TCP/IP port", widget=HiddenInput(), validators=[
        validators.NumberRange(min=1, max=65535)
    ])
    SECRET_KEY = HiddenField("Secret key", validators=[])
    SERVER_NAME = HiddenField("Server name", validators=[])
    MAX_TIME = IntegerField("Max relay run time", validators=[
        validators.NumberRange(min=1)
    ])
    MAX_CONCURRENT = IntegerField("Max concurrent running relays", validators=[
        validators.NumberRange(min=1)
    ])
    TIME_SELECTOR = RadioField(
        "Dashboard time selector",
        choices=[
            ("buttons", "Time buttons"),
            ("slider", "Time slider"),
        ],
    )
    BOARD_NAME = StringField("Board object name", validators=[std_length])
    CONNECTION_NAME = StringField("Board connection name", validators=[
        std_length
    ])
    RELAY_NAME = StringField("Relay object name", validators=[std_length])
    DEPENDENCY_NAME = StringField("Relay dependency name", validators=[
        std_length
    ])
    SEQUITUR_NAME = StringField("Sequence object name", validators=[
        std_length
    ])
    SEQUENCIA_NAME = StringField("Sequence entry name", validators=[
        std_length
    ])
    SCHEDULE_NAME = StringField("Schedule object name", validators=[
        std_length
    ])
    JOB_NAME = StringField("Scheduled job name", validators=[std_length])
    RUNNING_TIMES = FieldList(FormField(RunningTimeForm))
    submit = SubmitField()


class BoardForm(BasicForm):
    type = SelectField("Type", choices=[("PiPlates", "PiPlates")])
    index = SelectField("Index", coerce=int)
    active = BooleanField("Active")


class DependencyForm(Form):
    relay = SelectField(current_app.config["RELAY_NAME"].capitalize())
    spin_up = IntegerField("Spin up", validators=[
        validators.NumberRange(min=0, max=5)
    ])


class RelayForm(BasicForm):
    board = SelectField(current_app.config["BOARD_NAME"].capitalize())
    index = SelectField("Index", coerce=int)
    active = BooleanField("Active")
    visible = BooleanField("Visible")
    dependencies = FieldList(FormField(DependencyForm))


class SequorForm(Form):
    relay = SelectField(current_app.config["RELAY_NAME"].capitalize())
    minutes = IntegerField("Minutes", validators=[
        validators.NumberRange(min=1, max=60)]
    )


class SequiturForm(BasicForm):
    sequencia = FieldList(FormField(SequorForm))


class FixtureForm(Form):
    sequitur = SelectField(current_app.config["SEQUITUR_NAME"].capitalize())
    weekdays = SelectField(
        "Weekdays",
        widget=Select(multiple=True),
        render_kw={"size": 7},
        coerce=int,
    )
    time = TimeField("Time")


class ScheduleForm(BasicForm):
    active = BooleanField("Active")
    jobs = FieldList(FormField(FixtureForm))
