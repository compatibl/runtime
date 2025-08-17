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
import inspect
import logging
import time
from dataclasses import dataclass
from uuid import UUID
from cl.runtime.file.file_data import FileData
from cl.runtime.log.exceptions.user_error import UserError
from cl.runtime.records.record_mixin import RecordMixin
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_handlers_key import StubHandlersKey

_LOGGER = logging.getLogger(__name__)


def _log_method_info():  # TODO: Move into testing directory
    """Print information about the caller method using stack inspection."""

    # Get logger from TaskLog
    # Record method information from stack frame
    current_frame = inspect.currentframe()
    assert current_frame is not None

    outer_frame = current_frame.f_back
    assert outer_frame is not None

    method_name = outer_frame.f_code.co_name
    args, _, _, values = inspect.getargvalues(outer_frame)

    # Explicitly delete the frames to avoid circular references
    del outer_frame
    del current_frame

    # Log information
    params_output = ",".join(f"{arg}={values[arg]}" for arg in args)
    _LOGGER.info(f"Called {method_name}({params_output})")


@dataclass(slots=True, kw_only=True)
class StubHandlers(StubHandlersKey, RecordMixin):
    """Stub record base class."""

    def get_key(self) -> StubHandlersKey:
        return StubHandlersKey(stub_id=self.stub_id).build()

    def run_instance_method_1a(self) -> None:
        """Stub handler."""
        _log_method_info()

    def run_instance_method_1a_with_int_param(self, int_param: int) -> None:
        """Stub handler."""
        _log_method_info()

    def run_instance_method_1a_with_primitive_params(
        self,
        str_param: str,
        float_param: float,
        bool_param: bool,
        int_param: int,
        date_param: dt.date,
        time_param: dt.time,
        datetime_param: dt.datetime,
        uuid_param: UUID,
        bytes_param: bytes,
    ) -> None:
        """Stub handler."""
        _log_method_info()

    def run_instance_method_1b(self) -> None:
        """Stub handler."""
        _log_method_info()

    # TODO (Roman): Restore after supporting handlers with parameters
    def run_instance_method_2a_with_params(self, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        _log_method_info()
        _LOGGER.info(f"param_1={param_1} param_2={param_2}")

    # TODO (Roman): Restore after supporting handlers with parameters()
    def run_instance_method_2b(self, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        _log_method_info()

    # TODO (Roman): Restore after supporting handlers with parameters
    def run_instance_method_3a(self, *, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        _log_method_info()

    # TODO (Roman): Restore after supporting handlers with parameters()
    def run_instance_method_3b(self, *, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        _log_method_info()

    @classmethod
    def run_class_method_1a(cls) -> None:
        """Stub handler."""
        _log_method_info()

    @classmethod
    def run_class_method_1b(cls) -> None:
        """Stub handler."""
        _log_method_info()

    # TODO (Roman): Restore after supporting handlers with parameters
    @classmethod
    def run_class_method_2a_with_params(cls, param_1: str, param_2: str) -> None:
        """Stub handler."""
        _log_method_info()
        _LOGGER.info(f"param_1={param_1} param_2={param_2}")

    # TODO (Roman): Restore after supporting handlers with parameters
    @classmethod
    def run_class_method_2b(cls, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        _log_method_info()

    # TODO (Roman): Restore after supporting handlers with parameters
    @classmethod
    def run_class_method_3a(cls, *, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        _log_method_info()

    # TODO (Roman): Restore after supporting handlers with parameters
    @classmethod
    def run_class_method_3b(cls, *, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        _log_method_info()

    @staticmethod
    def run_static_method_1a() -> None:
        """Stub handler."""
        _log_method_info()

    @staticmethod
    def run_static_method_1b() -> None:
        """Stub handler."""
        _log_method_info()

    # TODO (Roman): Restore after supporting handlers with parameters
    @staticmethod
    def run_static_method_2a(param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        _log_method_info()

    # TODO (Roman): Restore after supporting handlers with parameters
    @staticmethod
    def run_static_method_2b(param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        _log_method_info()

    # TODO (Roman): Restore after supporting handlers with parameters
    @staticmethod
    def run_static_method_3a(*, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        _log_method_info()

    # TODO (Roman): Restore after supporting handlers with parameters
    @staticmethod
    def run_static_method_3b(*, param_1: str, param_2: str | None = None) -> None:
        """Stub handler."""
        _log_method_info()

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

    # TODO (Roman): Restore after supporting handlers with parameters
    def run_with_two_args(self, arg_1: str, arg_2: str) -> str:
        """Stub method."""
        return arg_1 + arg_2

    # TODO (Roman): Restore after supporting handlers with parameters
    def run_with_args_and_optional(self, arg_1: str, arg_2: str, arg_3: str | None = None) -> str:
        """Stub method."""
        return arg_1 + arg_2

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
        _log_method_info()
        _LOGGER.info(f"Binary_data len={len(pdf_file.file_bytes)}")

    @staticmethod
    def run_class_method_with_binary_param(pdf_file: FileData):
        """Stub method."""
        _log_method_info()
        _LOGGER.info(f"Binary_data len={len(pdf_file.file_bytes)}")

    def run_long_handler_with_error(self):
        for i in range(10):
            _LOGGER.info(f"Message {i}")
            time.sleep(3)
        raise RuntimeError("Error in handler.")

    def run_long_handler(self):
        for i in range(10):
            _LOGGER.info(f"Message {i}")
            time.sleep(3)
        _LOGGER.info("Finished.")

    # TODO (Roman): Uncomment for tasks/test_submit.
    # def run_save_to_db(self):
    #     """Stub method."""
    #     record_to_save = StubDataclass(id="saved_from_handler").build()
    #     active(DataSource).replace_one(record_to_save)
    #     _LOGGER.info(f"Record {record_to_save} has been saved to db from handler.")
