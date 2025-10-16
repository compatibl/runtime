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

from cl.runtime.contexts.context_manager import activate
from cl.runtime.db.data_source import DataSource
from cl.runtime.db.tenant_key import TenantKey
from cl.runtime.events.event_broker import EventBroker
from cl.runtime.tasks.celery.celery_queue import CeleryQueue


async def activate_auth_contexts():
    """Perform authorization code and activate contexts with user 'tenant'."""

    # TODO (Roman): Add settings to enable auth
    auth_enabled = False

    # If auth disabled don't create contexts isolated by tenant
    # Will be used common contexts by default
    if not auth_enabled:
        yield
    else:
        # TODO (Roman): Perform authentication to get user 'tenant'
        tenant = TenantKey(tenant_id="_Stub_Tenant")

        # Create and activate contexts with the authenticated user's tenant.
        # This is needed to ensure an isolated user environment within the API route call.
        with activate(DataSource(tenant=tenant).build()), activate(EventBroker.create(tenant=tenant)), activate(CeleryQueue(tenant=tenant, queue_id="Handler Queue").build()):
            yield