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
import traceback
from logging import LogRecord
from cl.runtime.contexts.db_context import DbContext
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.log.log_message import LogMessage
from cl.runtime.log.user_log_message import UserLogMessage
from cl.runtime.primitive.case_util import CaseUtil


class DbLogHandler(logging.Handler):
    """Handler to save logs to db."""

    @classmethod
    def _create_log_message(cls, record: LogRecord) -> LogMessage:
        """Create LogMessage object from LogRecord."""

        # Extract exception info.
        exc_info = getattr(record, "exc_info", None)
        exc = exc_info[1] if exc_info else None
        traceback_ = exc_info[2] if exc_info else None

        # For UserError create UserLogMessage.
        if exc is not None and isinstance(exc, UserError):
            log_message_class = UserLogMessage
        else:
            log_message_class = LogMessage

        # If exc_info is available add it to message. Limit traceback length.
        if exc and traceback_:
            # TODO (Roman): Configure max traceback length in the settings.
            # Join last 5 traceback lines.
            traceback_str = "".join(traceback.format_tb(traceback_)[-5:])
        else:
            traceback_str = None

        return log_message_class(
            timestamp=getattr(record, "timestamp", None),
            level=CaseUtil.upper_to_pascal_case(record.levelname),
            message=record.getMessage(),
            logger_name=record.name,
            readable_time=getattr(record, "readable_time", None),
            traceback=traceback_str,
            record_type=getattr(record, "type", None),
            handler_name=getattr(record, "handler", None),
            record_key=getattr(record, "key", None),
            task_run_id=getattr(record, "task_run_id", None),
        ).build()

    def emit(self, record):
        try:
            # Save LogMessage to current db context.
            log_message = self._create_log_message(record)
            DbContext.save_one(log_message)
        except Exception:
            self.handleError(record)
