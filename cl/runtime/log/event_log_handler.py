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
from logging import LogRecord

from cl.runtime.contexts.context_manager import active
from cl.runtime.events.event import Event
from cl.runtime.events.event_broker import EventBroker
from cl.runtime.events.event_kind import EventKind
from cl.runtime.events.log_event import LogEvent
from cl.runtime.primitive.case_util import CaseUtil


class EventLogHandler(logging.Handler):
    """Handler to publish log events."""

    @classmethod
    def _create_log_event(cls, record: LogRecord) -> LogEvent:
        """Create LogEvent object from LogRecord."""

        return LogEvent(
            timestamp=getattr(record, "timestamp", None),
            event_kind=EventKind.LOG,
            level=CaseUtil.upper_to_pascal_case(record.levelname),
            message=record.getMessage(),
            readable_time=getattr(record, "readable_time", None),
            record_type_name=getattr(record, "type", None),
            handler_name=getattr(record, "handler", None),
            record_key=getattr(record, "key", None),
            task_run_id=getattr(record, "task_run_id", None),
        ).build()

    def emit(self, record):

        try:
            # Publish log event
            log_event = self._create_log_event(record)
            event_broker = active(EventBroker)
            event_broker.sync_publish("events", log_event)

            # If log record level is Error or Warning - trigger additional Error or Warning event
            if record.levelno >= logging.ERROR:
                event_broker.sync_publish("events", Event(event_kind=EventKind.ERROR).build())
            elif record.levelno >= logging.WARNING:
                event_broker.sync_publish("events", Event(event_kind=EventKind.WARNING).build())

        except Exception:
            self.handleError(record)
