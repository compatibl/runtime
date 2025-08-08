# Copyright (C) 2023-present The Project Contributors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import os
import socket
import threading
from cl.runtime.contexts.context_manager import active_or_none
from cl.runtime.contexts.log_context import LogContext
from cl.runtime.db.data_source import DataSource
from cl.runtime.primitive.datetime_util import DatetimeUtil
from cl.runtime.primitive.timestamp import Timestamp
from cl.runtime.settings.log_settings import LogSettings
from cl.runtime.settings.project_settings import ProjectSettings

max_log_file_size_bytes = 1024 * 1024 * 10  # 10MB
"""Max log file in bytes, after this size is reached older records will be erased"""


def get_log_filename() -> str:
    """Generate log filename during import and use it throughout the session."""

    # TODO: Refactor to use a unique directory name instead
    # Generate log file name.
    log_settings = LogSettings.instance()
    log_filename_format = log_settings.log_filename_format
    match log_filename_format:
        case "prefix":
            # Filename is the prefix with .log extension.
            result = f"{log_settings.log_filename_prefix}.log"
        case "prefix-timestamp":
            # UTC timestamp to millisecond precision for the log file name.
            log_timestamp = DatetimeUtil.now()
            # Serialize assuming millisecond precision.
            log_timestamp_str = (
                log_timestamp.strftime("%Y-%m-%d-%H-%M-%S") + f"-{int(round(log_timestamp.microsecond / 1000)):03d}"
            )
            result = f"{log_settings.log_filename_prefix}-{log_timestamp_str}.log"
        case _:
            valid_choices = ["prefix", "prefix-timestamp"]
            raise RuntimeError(
                f"Unknown log filename format: {log_filename_format}, " f"valid choices are {', '.join(valid_choices)}"
            )

    # Create log directory and filename relative to project root.
    project_root = ProjectSettings.get_project_root()
    log_dir = os.path.join(project_root, "logs")
    result = os.path.join(log_dir, result)

    # Create log directory if it does not exist.
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    _log_filename = result
    return result


def _make_filter_below_level(below_level):
    """Log filter for condition log.level < level. Gets log "level" registered in logging module."""
    below_level = logging.getLevelName(below_level)

    def filter_(record):
        return record.levelno < below_level

    return filter_


def _make_filter_above_level(above_level):
    """
    Log filter for condition log.level >= level. Gets log "level" registered in logging module.
    Basically the same as setLevel() method.
    """
    above_level = logging.getLevelName(above_level)

    def filter_(record):
        return record.levelno >= above_level

    return filter_


def _make_filter_add_contextual_info(default_empty=None):
    """Add contextual attributes to log record."""

    _default_empty = default_empty

    def filter_(record):
        log_context = LogContext.current_or_none()

        type_and_handler = ""
        if log_context:
            if log_context.record_type is not None:
                type_and_handler += f" - {log_context.record_type}"

            if log_context.handler is not None:
                type_and_handler += f" - {log_context.handler}"

            if log_context.task_run_id is not None:
                type_and_handler += f" - run_id={log_context.task_run_id[-5:]}"

        # Type on which the handler is running
        record.type = log_context.record_type or _default_empty if log_context else _default_empty

        # Name of running handler
        record.handler = log_context.handler or _default_empty if log_context else _default_empty

        # Record key
        record.key = log_context.record_key or _default_empty if log_context else _default_empty

        # Combined type and handler name as single field in short format
        record.type_and_handler = type_and_handler

        # Task run id
        record.task_run_id = log_context.task_run_id or _default_empty if log_context else _default_empty

        # Time-ordered unique identifier
        if getattr(record, "timestamp", None) is None:
            record.timestamp = Timestamp.create()

        # Human-readable time
        record.readable_time = DatetimeUtil.to_str(Timestamp.to_datetime(record.timestamp))

        # PID of process
        record.pid = os.getpid()

        # Thread id
        record.tid = threading.get_ident()

        # Machine host name
        record.host = socket.gethostname()

        return True

    return filter_


def _make_filter_db_logs():
    """Filter logs to be stored in db."""

    def filter_(record):
        # Filter out third-party lib info logs
        third_party_logs = record.levelno <= logging.INFO and record.name.startswith(("uvicorn", "celery"))

        # Filter out if the log was created outside the DataSource
        outside_data_context = active_or_none(DataSource) is None

        return not any(
            (
                third_party_logs,
                outside_data_context,
            )
        )

    return filter_


# Empty config to suppress default celery logger. Used to propagate all logs to root logger.
celery_empty_logging_config = {"version": 1, "loggers": {"celery": {}}}

# Empty config to suppress default uvicorn logger. Used to propagate all logs to root logger.
uvicorn_empty_logging_config = {
    "version": 1,
    "loggers": {
        "uvicorn": {},
        "uvicorn.error": {},
        "uvicorn.access": {},
    },
}


logging_config = {
    "version": 1,
    "formatters": {
        "file_formatter": {
            "format": "%(readable_time)s - PID=%(pid)s - %(host)s - %(name)s - %(type)s - %(handler)s - %(key)s - "
            "%(task_run_id)s - %(levelname)s - %(message)s",
        },
        "console_formatter": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelname)s%(type_and_handler)s - %(message)s",
            "use_colors": None,
        },
    },
    "filters": {
        "below_error_level_filter": {
            "()": "cl.runtime.log.log_config._make_filter_below_level",
            "below_level": "ERROR",
        },
        "above_error_level_filter": {
            "()": "cl.runtime.log.log_config._make_filter_above_level",
            "above_level": "ERROR",
        },
        "add_contextual_info_filter": {"()": "cl.runtime.log.log_config._make_filter_add_contextual_info"},
        "add_contextual_info_filter_with_default": {
            "()": "cl.runtime.log.log_config._make_filter_add_contextual_info",
            "default_empty": ".",
        },
        "db_logs_filter": {"()": "cl.runtime.log.log_config._make_filter_db_logs"},
    },
    "handlers": {
        "file_handler": {
            "level": "INFO",
            "class": "concurrent_log_handler.ConcurrentRotatingFileHandler",
            "filename": get_log_filename(),
            "maxBytes": max_log_file_size_bytes,
            "backupCount": 0,  # Do not create backup files because each file has a timestamp.
            "filters": ["add_contextual_info_filter_with_default"],
            "formatter": "file_formatter",
        },
        "stderr_handler": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
            "filters": ["add_contextual_info_filter", "above_error_level_filter"],
            "formatter": "console_formatter",
        },
        "stdout_handler": {
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "filters": ["add_contextual_info_filter", "below_error_level_filter"],
            "formatter": "console_formatter",
        },
        "db_handler": {
            "level": "INFO",
            "filters": ["add_contextual_info_filter", "db_logs_filter"],
            "class": "cl.runtime.log.db_log_handler.DbLogHandler",
        },
        "event_handler": {
            "level": "INFO",
            "filters": ["add_contextual_info_filter", "db_logs_filter"],
            "class": "cl.runtime.log.event_log_handler.EventLogHandler",
        },
    },
    "loggers": {
        "": {
            "handlers": ["file_handler", "stderr_handler", "stdout_handler", "db_handler", "event_handler"],
            "level": "INFO",
        },
    },
}
