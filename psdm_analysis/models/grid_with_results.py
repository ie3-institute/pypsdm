import logging
from dataclasses import dataclass
from datetime import datetime
from typing import List

from psdm_analysis.models.input.container.grid_container import GridContainer
from psdm_analysis.models.input.container.participants_container import (
    SystemParticipantsContainer,
)
from psdm_analysis.models.input.enums import SystemParticipantsEnum
from psdm_analysis.models.result.res_container import ResultContainer
from psdm_analysis.models.result.grid.enhanced_node import EnhancedNodesResult
from psdm_analysis.models.result.grid.node import NodesResult
from psdm_analysis.models.result.participant.participant import ParticipantsResult
from psdm_analysis.models.result.participant.participants_res_container import (
    ParticipantsResultContainer,
)


@dataclass(frozen=True)
class GridWithResults:
    grid: GridContainer
    results: ResultContainer

    @classmethod
    def from_csv(
        cls,
        name: str,
        grid_path: str,
        grid_delimiter: str,
        result_path: str,
        result_delimiter: str,
        simulation_end: datetime = None,
        from_agg_results: bool = False,
    ) -> "GridWithResults":
        grid = GridContainer.from_csv(grid_path, grid_delimiter)

        if not grid:
            raise ValueError(f"Grid is empty. Is the path correct? {grid_path}")

        results = ResultContainer.from_csv(
            name,
            result_path,
            result_delimiter,
            simulation_end,
            grid.raw_grid,
            from_agg_results,
        )

        if not results:
            raise ValueError(f"Results are empty. Is the path correct? {result_path}")

        return GridWithResults(grid, results)

    def nodal_energies(self) -> dict[dict[str:float]]:
        return {
            uuid: self.nodal_energy(uuid) for uuid in self.grid.raw_grid.nodes.uuids()
        }

    def nodal_energy(self, uuid: str) -> dict[str:float]:
        return self.nodal_result(uuid).energy_consumption()

    def nodal_results(self) -> dict[str:ResultContainer]:
        return {
            node_uuid: self.nodal_result(node_uuid)
            for node_uuid in self.grid.node_participants_map.keys()
        }

    def nodal_result(self, node_uuid: str) -> "ResultContainer":
        node_participants = self.grid.node_participants_map[node_uuid]
        ems = self._safe_get_result(
            SystemParticipantsEnum.ENERGY_MANAGEMENT,
            list(node_participants.ems.uuids()),
            self.results.participants.ems,
        )
        loads = self._safe_get_result(
            SystemParticipantsEnum.LOAD,
            list(node_participants.loads.uuids()),
            self.results.participants.loads,
        )
        pvs = self._safe_get_result(
            SystemParticipantsEnum.PHOTOVOLTAIC_POWER_PLANT,
            list(node_participants.pvs.uuids()),
            self.results.participants.pvs,
        )
        wecs = self._safe_get_result(
            SystemParticipantsEnum.WIND_ENERGY_CONVERTER,
            list(node_participants.wecs.uuids()),
            self.results.participants.wecs,
        )
        storages = self._safe_get_result(
            SystemParticipantsEnum.STORAGE,
            list(node_participants.storages.uuids()),
            self.results.participants.storages,
        )
        fixed_feed_ins = self._safe_get_result(
            SystemParticipantsEnum.FIXED_FEED_IN,
            list(node_participants.fixed_feed_ins.uuids()),
            self.results.participants.fixed_feed_ins,
        )
        evcs = self._safe_get_result(
            SystemParticipantsEnum.EV_CHARGING_STATION,
            list(node_participants.evcs.uuids()),
            self.results.participants.evcs,
        )
        hps = self._safe_get_result(
            SystemParticipantsEnum.HEATP_PUMP,
            list(node_participants.hps.uuids()),
            self.results.participants.hps,
        )
        participants = ParticipantsResultContainer(
            ems, loads, fixed_feed_ins, pvs, wecs, storages, evcs, hps
        )

        return ResultContainer(
            name=node_uuid,
            nodes=NodesResult({node_uuid: self.results.nodes.nodes[node_uuid]}),
            participants=participants,
        )

    @staticmethod
    def _safe_get_result(
        participant: SystemParticipantsEnum,
        participant_uuids: List[str],
        participant_results: "ParticipantsResult",
    ) -> ParticipantsResult:
        # todo: link to corresponding SIMONA issue
        """
        Returns the corresponding participant results for a list of uuids. Missing results can happen in rare cases
        where SIMONA does not output single results for a system participant.

        :param participant_uuids: the participant uuids to look for
        :param participant_results: the corresponding results
        :return: mapping between uuids and results
        """
        res = dict()
        for participant_uuid in participant_uuids:
            if participant_uuid in participant_results.participants:
                res[participant_uuid] = participant_results.participants[
                    participant_uuid
                ]
            else:
                logging.debug(
                    "There is no result for result for participant "
                    + participant_uuid
                    + "within the participant results of the"
                    + str(type(participant_results))
                )
        return ParticipantsResult(participant, res)

    def em_results(
        self,
    ) -> [(SystemParticipantsContainer, ParticipantsResultContainer)]:
        uuid_to_connected_asset = self.grid.participants.ems.uuid_to_connected_assets()
        return [
            (
                self.grid.participants.subset(connected_assets + [em_uuid]),
                self.results.participants.subset(connected_assets + [em_uuid]),
            )
            for (em_uuid, connected_assets) in uuid_to_connected_asset.items()
        ]

    def build_enhanced_nodes_result(self):
        nodal_results = self.nodal_results()
        ps = {
            uuid: nodal_result.participants_p_agg()
            for uuid, nodal_result in nodal_results.items()
        }
        qs = {
            uuid: nodal_result.participants_q_agg()
            for uuid, nodal_result in nodal_results.items()
        }
        return EnhancedNodesResult.from_nodes_result(self.results.nodes, ps, qs)

    def find_participant_result_pair(self, uuid: str):
        return self.grid.participants.find_participant(
            uuid
        ), self.results.participants.find_participant_result(uuid)

    def filter_for_time_interval(self, start: datetime, end: datetime):
        nodes_res = self.results.nodes.filter_for_time_interval(start, end)
        participant_res = self.results.participants.filter_for_time_interval(start, end)
        return GridWithResults(
            self.grid, ResultContainer(self.results.name, nodes_res, participant_res)
        )
