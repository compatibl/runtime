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

import datetime as dt
import logging
import time
from dataclasses import dataclass
from uuid import UUID
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.file.file_data import FileData
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.qa.pytest.pytest_util import PytestUtil
from cl.runtime.records.record_mixin import RecordMixin
from cl.runtime.records.typename import typename
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_handlers_key import StubHandlersKey

_logger = logging.getLogger(__name__)


@dataclass(slots=True, kw_only=True)
class StubHandlers(StubHandlersKey, RecordMixin):
    """Stub record base class."""

    def get_key(self) -> StubHandlersKey:
        return StubHandlersKey(stub_id=self.stub_id).build()

    def run_instance_method_1a(self) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

    def run_instance_method_1a_with_int_param(self, int_param: int) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

        if not isinstance(int_param, int):
            raise RuntimeError(f"The type of 'int_param' is '{type(int_param)}' rather than {typename(int)}.")

    def run_instance_method_1a_with_primitive_params(
        self,
        str_param: str | None = None,
        float_param: float | None = None,
        bool_param: bool | None = None,
        int_param: int | None = None,
        date_param: dt.date | None = None,
        time_param: dt.time | None = None,
        datetime_param: dt.datetime | None = None,
        uuid_param: UUID | None = None,
        bytes_param: bytes | None = None,
    ) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

        if str_param is not None and not isinstance(str_param, str):
            raise RuntimeError(f"The type of 'str_param' is '{type(str_param)}' rather than {typename(str)} or None.")
        if float_param is not None and not isinstance(float_param, float):
            raise RuntimeError(
                f"The type of 'float_param' is '{type(float_param)}' rather than {typename(float)} or None."
            )
        if bool_param is not None and not isinstance(bool_param, bool):
            raise RuntimeError(
                f"The type of 'bool_param' is '{type(bool_param)}' rather than {typename(bool)} or None."
            )
        if int_param is not None and not isinstance(int_param, int):
            raise RuntimeError(f"The type of 'int_param' is '{type(int_param)}' rather than {typename(int)} or None.")
        if date_param is not None and not isinstance(date_param, dt.date):
            raise RuntimeError(
                f"The type of 'date_param' is '{type(date_param)}' rather than {typename(dt.date)} or None."
            )
        if time_param is not None and not isinstance(time_param, dt.time):
            raise RuntimeError(
                f"The type of 'time_param' is '{type(time_param)}' rather than {typename(dt.time)} or None."
            )
        if datetime_param is not None and not isinstance(datetime_param, dt.datetime):
            raise RuntimeError(
                f"The type of 'datetime_param' is '{type(datetime_param)}' rather than {typename(dt.datetime)} or None."
            )
        if uuid_param is not None and not isinstance(uuid_param, UUID):
            raise RuntimeError(
                f"The type of 'uuid_param' is '{type(uuid_param)}' rather than {typename(UUID)} or None."
            )
        if bytes_param is not None and not isinstance(bytes_param, bytes):
            raise RuntimeError(
                f"The type of 'bytes_param' is '{type(bytes_param)}' rather than {typename(bytes)} or None."
            )

    def run_instance_method_1b(self) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

    def run_instance_method_2a_with_params(self, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

        if not isinstance(param_1, str):
            raise RuntimeError(f"The type of 'param_1' is '{type(param_1)}' rather than {typename(str)}.")
        if param_2 is not None and not isinstance(param_2, str):
            raise RuntimeError(f"The type of 'param_2' is '{type(param_2)}' rather than {typename(str)} or None.")

    def run_instance_method_2b_with_params(self, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

        if not isinstance(param_1, str):
            raise RuntimeError(f"The type of 'param_1' is '{type(param_1)}' rather than {typename(str)}.")
        if param_2 is not None and not isinstance(param_2, str):
            raise RuntimeError(f"The type of 'param_2' is '{type(param_2)}' rather than {typename(str)} or None.")

    def run_instance_method_3a_with_params(self, *, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

        if not isinstance(param_1, str):
            raise RuntimeError(f"The type of 'param_1' is '{type(param_1)}' rather than {typename(str)}.")
        if param_2 is not None and not isinstance(param_2, str):
            raise RuntimeError(f"The type of 'param_2' is '{type(param_2)}' rather than {typename(str)} or None.")

    def run_instance_method_3b_with_params(self, *, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

        if not isinstance(param_1, str):
            raise RuntimeError(f"The type of 'param_1' is '{type(param_1)}' rather than {typename(str)}.")
        if param_2 is not None and not isinstance(param_2, str):
            raise RuntimeError(f"The type of 'param_2' is '{type(param_2)}' rather than {typename(str)} or None.")

    @classmethod
    def run_class_method_1a(cls) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

    @classmethod
    def run_class_method_1b(cls) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

    @classmethod
    def run_class_method_2a_with_params(cls, param_1: str, param_2: str) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

        if not isinstance(param_1, str):
            raise RuntimeError(f"The type of 'param_1' is '{type(param_1)}' rather than {typename(str)}.")
        if not isinstance(param_2, str):
            raise RuntimeError(f"The type of 'param_2' is '{type(param_2)}' rather than {typename(str)}.")

    @classmethod
    def run_class_method_2b_with_params(cls, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

        if not isinstance(param_1, str):
            raise RuntimeError(f"The type of 'param_1' is '{type(param_1)}' rather than {typename(str)}.")
        if param_2 is not None and not isinstance(param_2, str):
            raise RuntimeError(f"The type of 'param_2' is '{type(param_2)}' rather than {typename(str)} or None.")

    @classmethod
    def run_class_method_3a_with_params(cls, *, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

        if not isinstance(param_1, str):
            raise RuntimeError(f"The type of 'param_1' is '{type(param_1)}' rather than {typename(str)}.")
        if param_2 is not None and not isinstance(param_2, str):
            raise RuntimeError(f"The type of 'param_2' is '{type(param_2)}' rather than {typename(str)} or None.")

    @classmethod
    def run_class_method_3b_with_params(cls, *, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

        if not isinstance(param_1, str):
            raise RuntimeError(f"The type of 'param_1' is '{type(param_1)}' rather than {typename(str)}.")
        if param_2 is not None and not isinstance(param_2, str):
            raise RuntimeError(f"The type of 'param_2' is '{type(param_2)}' rather than {typename(str)} or None.")

    @staticmethod
    def run_static_method_1a() -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

    @staticmethod
    def run_static_method_1b() -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

    @staticmethod
    def run_static_method_2a_with_params(param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

        if not isinstance(param_1, str):
            raise RuntimeError(f"The type of 'param_1' is '{type(param_1)}' rather than {typename(str)}.")
        if param_2 is not None and not isinstance(param_2, str):
            raise RuntimeError(f"The type of 'param_2' is '{type(param_2)}' rather than {typename(str)} or None.")

    @staticmethod
    def run_static_method_2b_with_params(param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

        if not isinstance(param_1, str):
            raise RuntimeError(f"The type of 'param_1' is '{type(param_1)}' rather than {typename(str)}.")
        if param_2 is not None and not isinstance(param_2, str):
            raise RuntimeError(f"The type of 'param_2' is '{type(param_2)}' rather than {typename(str)} or None.")

    @staticmethod
    def run_static_method_3a_with_params(*, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

        if not isinstance(param_1, str):
            raise RuntimeError(f"The type of 'param_1' is '{type(param_1)}' rather than {typename(str)}.")
        if param_2 is not None and not isinstance(param_2, str):
            raise RuntimeError(f"The type of 'param_2' is '{type(param_2)}' rather than {typename(str)} or None.")

    @staticmethod
    def run_static_method_3b_with_params(*, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        PytestUtil.log_method_info(_logger)

        if not isinstance(param_1, str):
            raise RuntimeError(f"The type of 'param_1' is '{type(param_1)}' rather than {typename(str)}.")
        if param_2 is not None and not isinstance(param_2, str):
            raise RuntimeError(f"The type of 'param_2' is '{type(param_2)}' rather than {typename(str)} or None.")

    # TODO (Roman): Restore after supporting handlers with parameters
    # def run_with_args(
    #     self,
    #     int_arg: int,
    #     datetime_arg: dt.datetime,
    #     enum_arg: StubIntEnum,
    #     data_arg: Any,
    # ) -> None:
    #     _LOGGER.info(
    #         f"handler_with_arguments(int_arg={int_arg} datetime_arg={datetime_arg}"
    #         f"enum_arg={enum_arg} data_arg={data_arg})"
    #     )

    def run_sum_params(self, param_1: str, param_2: str) -> str:
        """Stub method."""
        if not isinstance(param_1, str):
            raise RuntimeError(f"The type of 'param_1' is '{type(param_1)}' rather than {typename(str)}.")
        if not isinstance(param_2, str):
            raise RuntimeError(f"The type of 'param_2' is '{type(param_2)}' rather than {typename(str)}.")

        return param_1 + param_2

    # TODO (Roman): Restore after supporting handlers with parameters
    # def run_with_reserved_param_name(self, from_: dt.date = None) -> dt.date:
    #     """Stub method."""
    #     return from_

    def run_with_error(self):
        """Stub method."""
        raise RuntimeError("Error in handler.")

    def run_with_user_error(self):
        """Stub method."""
        raise UserError("User error in handler.")

    def run_instance_method_with_binary_param(self, pdf_file: FileData, note_param: str):
        """Stub method."""
        PytestUtil.log_method_info(_logger)
        _logger.info(f"Binary_data len={len(pdf_file.file_bytes)}")

        if not isinstance(pdf_file, FileData):
            raise RuntimeError(f"The type of 'pdf_file' is '{type(pdf_file)}' rather than {typename(FileData)}.")
        if not isinstance(note_param, str):
            raise RuntimeError(f"The type of 'note_param' is '{type(note_param)}' rather than {typename(str)}.")

    @staticmethod
    def run_class_method_with_binary_param(pdf_file: FileData):
        """Stub method."""
        PytestUtil.log_method_info(_logger)
        _logger.info(f"Binary_data len={len(pdf_file.file_bytes)}")

        if not isinstance(pdf_file, FileData):
            raise RuntimeError(f"The type of 'pdf_file' is '{type(pdf_file)}' rather than {typename(FileData)}.")

    def run_long_handler_with_error(self):
        for i in range(10):
            _logger.info(f"Message {i}")
            time.sleep(3)
        raise RuntimeError("Error in handler.")

    def run_long_handler(self):
        for i in range(10):
            _logger.info(f"Message {i}")
            time.sleep(3)
        _logger.info("Finished.")

    @staticmethod
    def run_long_static_handler():
        for i in range(10):
            _logger.info(f"Message {i}")
            time.sleep(3)
        _logger.info("Finished.")

    # TODO (Roman): Restore after supporting submit_task inside handler
    # @classmethod
    # def run_generate_list_of_long_handlers(cls):
    #     """Generate a lot of long handlers."""
    #     record_type = TypeInfo.from_type_name(cls.__name__)
    #     long_handler_name = cls.run_long_handler.__name__
    #     label = f"{typename(record_type)};{long_handler_name}"
    #     task_queue = active(TaskQueue)
    #     handler_task = ClassMethodTask(
    #         label=label,
    #         queue=task_queue.get_key(),
    #         type_=record_type,
    #         method_name=long_handler_name,
    #     )
    #
    #     for i in range(100):
    #         task = handler_task.build()
    #         active(DataSource).replace_one(task, commit=True)
    #         task_queue.submit_task(task)

    def run_method_persist_record(self, record: StubDataclass):
        """Stub method."""
        if not isinstance(record, StubDataclass):
            raise RuntimeError(f"The type of 'record' is '{type(record)}' rather than {typename(StubDataclass)}.")

        active(DataSource).replace_one(record, commit=True)
        _logger.info(f"Record {record} has been saved to db from handler.")
