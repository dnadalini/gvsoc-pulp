#
# Copyright (C) 2025 ETH Zurich, University of Bologna and Fondazione ChipsIT
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Authors: Alessandro Nadalini (alessandro.nadalini3@unibo.it)
#

import gvsoc.systree
import memory.memory as memory
import interco.router as router
import gdbserver.gdbserver
from pulp.stdout.stdout_v3 import Stdout

from pulp.chips.democritos.democritos_arch import DemocritosArch
from pulp.chips.democritos.cluster import *

class Democritos_S_Tile(gvsoc.systree.Component):
    def __init__(self, parent, name, parser, tid: int=0, cluster_config_file: str=None):
        super().__init__(parent, name)

        # PULP cluster - TODO: INTEGRATION OF FractalSync
        cluster = Cluster(self, "s-tile-cluster", config_file=cluster_config_file, cid=0)

        # Bind fetch enable
        for pe in range(0, cluster.conf.get_property('nb_pe', int)):
            self.bind(self, 'fetchen', cluster, 'halt_pe%d' % pe)

        # Fake UART
        stdout = Stdout(self, f'tile-{tid}-stdout', max_cluster=DemocritosArch.NB_CLUSTERS, max_core_per_cluster=1, user_set_core_id=0, user_set_cluster_id=0)

        # AXI xbar
        tile_xbar = router.Router(self, f'tile-{tid}-xbar', bandwidth=4, latency=2)

        # Bind cluster AXI master port to tile xbar
        gvsoc.systree.SlaveItf(self, 'soc', signature='io')
        self.bind(cluster, 'soc', self, 'soc')
        self.itf_bind('soc', tile_xbar.i_INPUT(), composite_bind=True)
        
        # Bind cluster AXI slave port to tile xbar
        tile_xbar.add_mapping('cluster_slave',
                             base=DemocritosArch.CLUSTER_ADDR_START,
                             size=DemocritosArch.CLUSTER_ADDR_SIZE,
                             remove_offset=0)
        self.bind(tile_xbar, 'cluster_slave', cluster, 'input')


        # Bind AXI xbar to NI for the access to the external L2 memory
        tile_xbar.o_MAP(self.__i_NARROW_OUTPUT(), name='axi-to-off-tile-l2-mem',
                        base=DemocritosArch.L2_ADDR_START,
                        size=DemocritosArch.L2_SIZE, rm_base=False)

        # Bind AXI xbar to access the kill module
        tile_xbar.o_MAP(self.__i_KILLER_OUTPUT(), name='Kill-sim-mem',
                        base=DemocritosArch.TEST_END_ADDR_START,
                        size=DemocritosArch.TEST_END_SIZE, rm_base=False)

        # Bind AXI xbar to write to fake UART
        tile_xbar.o_MAP(stdout.i_INPUT(), name='local-uart-mem',
                        base=DemocritosArch.STDOUT_START,
                        size=DemocritosArch.STDOUT_SIZE, rm_base=False)
        
        # Bind ELF loader to AXI xbar
        self.__o_LOADER(tile_xbar.i_INPUT())
        
        # Bind NI to AXI xbar for the access to the cluster
        self.__o_NARROW_INPUT(tile_xbar.i_INPUT())

        # Bind FractalSync ports - TODO: INTEGRATION OF MEMORY-MAPPED MODEL OF FractalSync

        # Enable debug
        gdbserver.gdbserver.Gdbserver(self, 'gdbserver')

    # Cluster clocks
    def i_REF_CLK(self) -> gvsoc.systree.SlaveItf:
        return gvsoc.systree.SlaveItf(self, 'ref_clk', signature='wire<bool>')

    def i_CLK(self) -> gvsoc.systree.SlaveItf:
        return gvsoc.systree.SlaveItf(self, 'clock_in', signature='wire<bool>')
    
    # East West port to FractalSync
    def __o_SLAVE_EAST_WEST_FRACTAL(self) -> gvsoc.systree.SlaveItf:
        return gvsoc.systree.SlaveItf(self, 'cluster_2_east_west_fractal', signature='wire<PortReq<uint32_t>*>')

    def o_SLAVE_EAST_WEST_FRACTAL(self, itf: gvsoc.systree.SlaveItf):
        self.itf_bind('cluster_2_east_west_fractal', itf, signature='wire<PortReq<uint32_t>*>')

    def __i_SLAVE_EAST_WEST_FRACTAL(self, itf: gvsoc.systree.SlaveItf):
        self.itf_bind('east_west_fractal_2_cluster', itf, signature='wire<PortReq<uint32_t>*>', composite_bind=True)

    def i_SLAVE_EAST_WEST_FRACTAL(self) -> gvsoc.systree.SlaveItf:
        return gvsoc.systree.SlaveItf(self, 'east_west_fractal_2_cluster', signature='wire<PortReq<uint32_t>*>')

    # North South port to FractalSync
    def __o_SLAVE_NORTH_SOUTH_FRACTAL(self) -> gvsoc.systree.SlaveItf:
        return gvsoc.systree.SlaveItf(self, 'cluster_2_north_south_fractal', signature='wire<PortReq<uint32_t>*>')

    def o_SLAVE_NORTH_SOUTH_FRACTAL(self, itf: gvsoc.systree.SlaveItf):
        self.itf_bind('cluster_2_north_south_fractal', itf, signature='wire<PortReq<uint32_t>*>')

    def __i_SLAVE_NORTH_SOUTH_FRACTAL(self, itf: gvsoc.systree.SlaveItf):
        self.itf_bind('north_south_fractal_2_cluster', itf, signature='wire<PortReq<uint32_t>*>', composite_bind=True)

    def i_SLAVE_NORTH_SOUTH_FRACTAL(self) -> gvsoc.systree.SlaveItf:
        return gvsoc.systree.SlaveItf(self, 'north_south_fractal_2_cluster', signature='wire<PortReq<uint32_t>*>')

    # East West port to neighbour FractalSync
    def __o_SLAVE_EAST_WEST_FRACTAL(self) -> gvsoc.systree.SlaveItf:
        return gvsoc.systree.SlaveItf(self, 'cluster_2_east_west_neighbour_fractal', signature='wire<PortReq<uint32_t>*>')

    def o_SLAVE_EAST_WEST_NEIGHBOUR_FRACTAL(self, itf: gvsoc.systree.SlaveItf):
        self.itf_bind('cluster_2_east_west_neighbour_fractal', itf, signature='wire<PortReq<uint32_t>*>')

    def __i_SLAVE_EAST_WEST_NEIGHBOUR_FRACTAL(self, itf: gvsoc.systree.SlaveItf):
        self.itf_bind('east_west_neighbour_fractal_2_cluster', itf, signature='wire<PortReq<uint32_t>*>', composite_bind=True)

    def i_SLAVE_EAST_WEST_NEIGHBOUR_FRACTAL(self) -> gvsoc.systree.SlaveItf:
        return gvsoc.systree.SlaveItf(self, 'east_west_neighbour_fractal_2_cluster', signature='wire<PortReq<uint32_t>*>')

    # North South port to neighbour FractalSync
    def __o_SLAVE_NORTH_SOUTH_NEIGHBOUR_FRACTAL(self) -> gvsoc.systree.SlaveItf:
        return gvsoc.systree.SlaveItf(self, 'cluster_2_north_south_neighbour_fractal', signature='wire<PortReq<uint32_t>*>')

    def o_SLAVE_NORTH_SOUTH_NEIGHBOUR_FRACTAL(self, itf: gvsoc.systree.SlaveItf):
        self.itf_bind('cluster_2_north_south_neighbour_fractal', itf, signature='wire<PortReq<uint32_t>*>')

    def __i_SLAVE_NORTH_SOUTH_NEIGHBOUR_FRACTAL(self, itf: gvsoc.systree.SlaveItf):
        self.itf_bind('north_south_neighbour_fractal_2_cluster', itf, signature='wire<PortReq<uint32_t>*>', composite_bind=True)

    def i_SLAVE_NORTH_SOUTH_NEIGHBOUR_FRACTAL(self) -> gvsoc.systree.SlaveItf:
        return gvsoc.systree.SlaveItf(self, 'north_south_neighbour_fractal_2_cluster', signature='wire<PortReq<uint32_t>*>')

    # Output (master) port to L2 off-tile memory
    def o_NARROW_OUTPUT(self, itf: gvsoc.systree.SlaveItf):
        self.itf_bind('narrow_output', itf, signature='io')

    def __i_NARROW_OUTPUT(self) -> gvsoc.systree.SlaveItf:
        return gvsoc.systree.SlaveItf(self, 'narrow_output', signature='io')

    def i_NARROW_INPUT(self) -> gvsoc.systree.SlaveItf:
        return gvsoc.systree.SlaveItf(self, 'narrow_input', signature='io')

    def __o_NARROW_INPUT(self, itf: gvsoc.systree.SlaveItf):
        self.itf_bind('narrow_input', itf, signature='io', composite_bind=True)

    # Input port for the loader
    def i_LOADER(self) -> gvsoc.systree.SlaveItf:
        return gvsoc.systree.SlaveItf(self, 'loader', signature='io')

    def __o_LOADER(self, itf: gvsoc.systree.SlaveItf):
        self.itf_bind('loader', itf, signature='io', composite_bind=True)
    
    # Maybe the following ones are't needed
    def i_FETCHEN(self) -> gvsoc.systree.SlaveItf:
        return gvsoc.systree.SlaveItf(self, 'fetchen', signature='wire<bool>')

    def __o_FETCHEN(self, itf: gvsoc.systree.SlaveItf):
        self.itf_bind('fetchen', itf, signature='wire<bool>', composite_bind=True)

    def i_ENTRY(self) -> gvsoc.systree.SlaveItf:
        return gvsoc.systree.SlaveItf(self, 'entry', signature='wire<uint64_t>')

    def __o_ENTRY(self, itf: gvsoc.systree.SlaveItf):
        self.itf_bind('entry', itf, signature='wire<uint64_t>', composite_bind=True)

    # Killer port
    def o_KILLER_OUTPUT(self, itf: gvsoc.systree.SlaveItf):
        self.itf_bind('killer_output', itf, signature='io')

    def __i_KILLER_OUTPUT(self) -> gvsoc.systree.SlaveItf:
        return gvsoc.systree.SlaveItf(self, 'killer_output', signature='io')

