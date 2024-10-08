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


class UserError(Exception):
    """Custom exception for user-related errors."""

    def __init__(self, message="A user error occurred", username=None):
        super().__init__(message)
        self.username = username

    def __str__(self):
        message = f"UserError: {self.args[0]}"
        if self.username:
            message += f" (User: {self.username})"
        return message
