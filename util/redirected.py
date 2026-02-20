from functools import wraps
from flask import flash, redirect, url_for
from werkzeug.exceptions import NotFound


def simple_past(verb: str):
    if (
        verb[-1] in ['b', 'd', 'm', 'n', 'p'] and
        verb[-2] != verb[-1]
    ) or (
        verb[-1] == 'g' and
        verb[-2:-1] != "ng"
    ):
        verb += verb[-1] + "ed"
    elif verb[-1] == 'e':
        verb += 'd'
    else:
        verb += "ed"
    return verb


def redirected(collection, item_name, default_route):
    def redirected(on_success=default_route, on_error=default_route):
        def decorator_redirect(func):
            @wraps(func)
            def wrapper_redirect(*args, **kwargs):
                try:
                    if list(kwargs.values())[0] not in collection:
                        raise NotFound()
                    else:
                        obj_name = collection[list(kwargs.values())[0]].name
                    func(*args, **kwargs)
                except Exception as e:
                    if hasattr(e, "message"):
                        flash(e.message, "caution")
                    else:
                        flash(repr(e), "caution")
                    return redirect(url_for(on_error))
                flash(
                    " ".join(
                        [
                            item_name.capitalize(),
                            obj_name,
                            simple_past(func.__name__) + '.',
                        ]
                    ),
                    "success"
                )
                return redirect(url_for(on_success))
            return wrapper_redirect
        return decorator_redirect
    return redirected
