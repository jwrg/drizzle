from flask_wtf import FlaskForm
from wtforms import (
    Form,
    FieldList,
    FormField,
    SelectField,
    BooleanField,
    IntegerField,
    StringField,
    SubmitField,
    validators
)
from wtforms.widgets import html_params


class ButtonWidget:
    input_type = 'button'

    html_params = staticmethod(html_params)

    def __call__(self, field, **kwargs):
        kwargs.setdefault('id', field.id)
        kwargs.setdefault('type', self.input_type)
        if 'value' not in kwargs:
            kwargs['value'] = field._value()

        return '<button {params}>{label}</button>'.format(
            params=self.html_params(name=field.name, **kwargs),
            label=field.label.text
        )


class ButtonField(StringField):
    widget = ButtonWidget()


class BasicForm(FlaskForm):
    name = StringField('Name', validators=[validators.Length(min=4, max=64)])
    description = StringField('Description', validators=[
                              validators.Length(max=255)])
    submit = SubmitField()


class BoardForm(BasicForm):
    type = SelectField('Type', choices=[('PiPlates', 'PiPlates')])
    index = SelectField('Index', coerce=int)
    active = BooleanField('Active')


class DependencyForm(Form):
    relay = SelectField('Relay')
    spin_up = IntegerField('Spin up', validators=[
                           validators.NumberRange(min=0, max=5)])


class RelayForm(BasicForm):
    board = SelectField('Board')
    index = SelectField('Index', coerce=int)
    max_time = IntegerField('Max time', validators=[
                            validators.NumberRange(min=1, max=60)])
    default_time = IntegerField('Default time', validators=[
                                validators.NumberRange(min=1, max=60)])
    active = BooleanField('Active')
    visible = BooleanField('Visible')
    requires = FieldList(FormField(DependencyForm))


class SequorForm(Form):
    relay = SelectField('Relay')
    minutes = IntegerField('Minutes', validators=[
                           validators.NumberRange(min=1, max=60)])


class SequiturForm(BasicForm):
    sequence = FieldList(FormField(SequorForm))


class FixtureForm(Form):
    sequence = SelectField('Sequence')
    weekday = SelectField('Weekday', coerce=int)
    hour = IntegerField('Hour', validators=[
        validators.NumberRange(min=1, max=24)])
    minute = IntegerField('Minute', validators=[
        validators.NumberRange(min=0, max=59)])


class ScheduleForm(BasicForm):
    active = BooleanField('Active')
    jobs = FieldList(FormField(FixtureForm))
