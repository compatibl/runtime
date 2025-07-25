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
from cl.runtime.configs.config import Config
from cl.runtime.contexts.db_context import DbContext
from stubs.cl.runtime import StubDataclass
from stubs.cl.runtime import StubDataclassComposite
from stubs.cl.runtime import StubDataclassDerived
from stubs.cl.runtime import StubDataclassDictFields
from stubs.cl.runtime import StubDataclassDictListFields
from stubs.cl.runtime import StubDataclassDoubleDerived
from stubs.cl.runtime import StubDataclassListDictFields
from stubs.cl.runtime import StubDataclassListFields
from stubs.cl.runtime import StubDataclassNestedFields
from stubs.cl.runtime import StubDataclassOptionalFields
from stubs.cl.runtime import StubDataclassOtherDerived
from stubs.cl.runtime import StubDataclassPrimitiveFields
from stubs.cl.runtime import StubDataclassSingleton
from stubs.cl.runtime import StubDataViewers
from stubs.cl.runtime import StubHandlers
from stubs.cl.runtime import StubMediaViewers
from stubs.cl.runtime import StubPlotViewers
from stubs.cl.runtime.plots.stub_group_bar_plots import StubGroupBarPlots
from stubs.cl.runtime.plots.stub_heat_map_plots import StubHeatMapPlots
from stubs.cl.runtime.plots.stub_line_plots import StubLinePlots
from stubs.cl.runtime.records.for_dataclasses.stub_dataclass_dynamic import StubDataclassDynamic


@dataclass(slots=True, kw_only=True)
class StubRuntimeConfig(Config):
    """Save stub records to storage."""

    def run_configure(self) -> None:
        self.configure_records()
        self.configure_plots()

    @classmethod
    def configure_records(cls) -> None:
        """Populate the current or default database with stub records."""

        # Create stub instances
        stub_dataclass_composite = [StubDataclassComposite(primitive=f"abc{i}") for i in range(10)]
        stub_dataclass_records = [StubDataclass(id=f"A{i}") for i in range(10)]
        stub_dataclass_nested_fields = [StubDataclassNestedFields(id=f"B{i}") for i in range(10)]
        stub_dataclass_deriveds = [StubDataclassDerived(id=f"C{i}") for i in range(10)]
        stub_dataclass_double_deriveds = [StubDataclassDoubleDerived(id=f"D{i}") for i in range(10)]
        stub_dataclass_other_deriveds = [StubDataclassOtherDerived(id=f"E{i}") for i in range(10)]
        stub_dataclass_list_fields_records = [StubDataclassListFields(id=f"F{i}") for i in range(10)]
        stub_dataclass_optional_fields_records = [StubDataclassOptionalFields(id=f"G{i}") for i in range(10)]
        stub_dataclass_dict_fields_records = [StubDataclassDictFields(id=f"H{i}") for i in range(10)]
        stub_dataclass_dict_list_fields_records = [StubDataclassDictListFields(id=f"I{i}") for i in range(10)]
        stub_dataclass_list_dict_fields_records = [StubDataclassListDictFields(id=f"J{i}") for i in range(10)]
        stub_dataclass_primitive_fields_records = [
            StubDataclassPrimitiveFields(key_str_field=f"K{i}") for i in range(10)
        ]

        stub_dataclass_singleton_record = [StubDataclassSingleton()]
        stub_handlers_records = [StubHandlers(stub_id=f"M{i}") for i in range(10)]

        # Records with stub viewers
        stub_viewers_records = [
            StubDataViewers(stub_id=f"StubDataViewers"),
            StubPlotViewers(stub_id=f"StubPlotViewers"),
            StubMediaViewers(stub_id=f"StubMediaViewers"),
        ]

        stub_polymorphic_records = [
            StubDataclassDynamic(table_field="PolymorphicTable1", key_field="stub_key1", record_field="stub_record1"),
            StubDataclassDynamic(table_field="PolymorphicTable1", key_field="stub_key2", record_field="stub_record2"),
            StubDataclassDynamic(table_field="PolymorphicTable2", key_field="stub_key3", record_field="stub_record3"),
            StubDataclassDynamic(table_field="PolymorphicTable2", key_field="stub_key4", record_field="stub_record4"),
        ]

        all_records = [
            *stub_dataclass_composite,
            *stub_dataclass_records,
            *stub_dataclass_nested_fields,
            *stub_dataclass_deriveds,
            *stub_dataclass_double_deriveds,
            *stub_dataclass_other_deriveds,
            *stub_dataclass_optional_fields_records,
            # TODO: Restore after supporting dt.date and dt.time for Mongo: *stub_dataclass_list_fields_records,
            # TODO: Restore after supporting dt.date and dt.time for Mongo: *stub_dataclass_dict_fields_records,
            # TODO: Restore after supporting dt.date and dt.time for Mongo: *stub_dataclass_dict_list_fields_records,
            # TODO: Restore after supporting dt.date and dt.time for Mongo: *stub_dataclass_list_dict_fields_records,
            # TODO: Restore after supporting dt.date and dt.time for Mongo: *stub_dataclass_primitive_fields_records,
            *stub_dataclass_singleton_record,
            *stub_viewers_records,
            *stub_handlers_records,
            *stub_polymorphic_records,
        ]

        # Build and save to DB
        DbContext.save_many(record.build() for record in all_records)

    def configure_plots(self) -> None:
        """Configure plots."""

        # GroupBarPlot
        DbContext.save_many(
            (
                StubGroupBarPlots.get_single_group_plot(self.config_id + "stub_group_bar_plots.single_group"),
                StubGroupBarPlots.get_4_groups_2_bars_plot(self.config_id + "stub_group_bar_plots.4_groups_2_bars"),
                StubGroupBarPlots.get_4_groups_5_bars(self.config_id + "stub_group_bar_plots.4_groups_5_bars"),
            )
        )

        # HeatMapPlot
        DbContext.save_many((StubHeatMapPlots.get_basic_plot(self.config_id + "stub_heat_map_plots.basic"),))

        # LinePlot
        DbContext.save_many(
            (
                StubLinePlots.get_one_line_plot(self.config_id + "stub_line_plots.one_line"),
                StubLinePlots.get_two_line_plot(self.config_id + "stub_line_plots.two_line"),
            )
        )
