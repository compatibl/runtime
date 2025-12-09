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

import pytest
from typing import Any
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.qa.qa_client import QaClient
from cl.runtime.routers.auth.me_response import MeResponse
from cl.runtime.routers.auth.me_response import _get_user_secrets_public_key


def get_expected_result() -> dict[str, Any]:
    """Get expected result for the user."""

    # Get user from the request or use default value if not specified
    user = active(DataSource).tenant.tenant_id

    return {
        "Id": user,
        "Username": user,
        "FirstName": user,
        "LastName": None,
        "Email": None,
        "Scopes": ["Read", "Write", "Execute", "Developer"],
        "UserSecretsPublicKey": _get_user_secrets_public_key(),
    }


def test_method(default_db_fixture):
    """Test coroutine for /auth/me route."""

    # Run the coroutine wrapper added by the FastAPI decorator and get the result
    result = MeResponse.get_me()

    # Check the result
    expected_result = get_expected_result()
    assert result == MeResponse(**expected_result)


def test_api(default_db_fixture):
    """Test REST API for /auth/me route."""
    with QaClient() as test_client:
        response = test_client.get("/auth/me")
        assert response.status_code == 200
        result = response.json()

        # Check result
        expected_result = get_expected_result()
        assert result == expected_result


if __name__ == "__main__":
    pytest.main([__file__])
