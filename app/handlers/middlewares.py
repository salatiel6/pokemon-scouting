from typing import Any

from flask import Flask, Response, request

from app.handlers.logger import logger


def log_request_info() -> None:
    """
    Logs information about incoming HTTP requests before they are processed.

    This function is executed before each request. It skips logging for requests
    to static files or specific prefixes and logs the HTTP method and path for other requests.

    :return: None
    """
    if not request.path.startswith("/static/") and request.path != "/health":
        logger.debug(f"{request.method} {request.path}")


def log_response_info(response: Response) -> Any:
    """
    Logs information about HTTP responses after they are processed.

    This function is executed after each request. It skips logging for responses
    to static files or specific prefixes. For responses with status codes outside
    the range of 200–399, it logs an error message.

    :param response: The HTTP response object to be logged and returned.

    :return: The same HTTP response object, unmodified.
    """
    if not request.path.startswith("/static/") and request.path != "/health":
        if 200 <= response.status_code < 400:
            logger.info(response.get_data(as_text=True))
        else:
            logger.error(f"{response.status_code} {request.method} {request.path}")

    return response


def register_middlewares(app: Flask) -> None:
    """
    Registers request/response middleware handlers on the Flask application.

    This function wires the request logger to run before each request and the
    response logger to run after each request.

    :param app: A Flask application instance

    :return: None
    """
    # Register the middlewares without using nested functions or decorators
    app.before_request(log_request_info)
    app.after_request(log_response_info)
