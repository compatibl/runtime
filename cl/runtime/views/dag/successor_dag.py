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

from dataclasses import dataclass
from cl.runtime import RecordMixin
from cl.runtime.contexts.context_manager import active
from cl.runtime.db.data_source import DataSource
from cl.runtime.records.for_dataclasses.extensions import required
from cl.runtime.view.dag.dag import Dag
from cl.runtime.views.dag.successor_dag_key import SuccessorDagKey
from cl.runtime.views.dag.successor_dag_node import SuccessorDagNode
from cl.runtime.views.dag.successor_dag_node_key import SuccessorDagNodeKey


@dataclass(slots=True, kw_only=True)
class SuccessorDag(SuccessorDagKey, RecordMixin):
    """Directed acyclic graph (DAG) where each node defines its successors."""

    title: str = required()
    """Title of the DAG."""

    root_node: SuccessorDagNodeKey = required()
    """Root node of the DAG."""

    def get_key(self) -> SuccessorDagKey:
        return SuccessorDagKey(dag_id=self.dag_id).build()

    def view_dag(self) -> Dag | None:
        """DAG view."""
        if self.root_node is None:
            return None

        root_node = active(DataSource).load_one(self.root_node, cast_to=SuccessorDagNodeKey)

        if root_node is None:
            return None

        return SuccessorDagNode.build_dag(node=root_node)
