from functools import wraps
from flask import flash, redirect, url_for
from werkzeug.exceptions import NotFound
from util.filters import (
    filter_capitalize_all as capitalize,
    filter_simple_past as simple_past
)


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
                            capitalize(item_name),
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
