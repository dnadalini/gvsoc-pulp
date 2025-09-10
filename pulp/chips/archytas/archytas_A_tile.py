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

import gvsoc.systree
import memory.memory as memory
import interco.router as router
import gdbserver.gdbserver
from pulp.stdout.stdout_v3 import Stdout

import pulp.cpu.iss.pulp_cores as iss
from pulp.cluster.l1_interleaver import L1_interleaver
from pulp.light_redmule.hwpe_interleaver import HWPEInterleaver
from pulp.snitch.snitch_cluster.dma_interleaver import DmaInterleaver
from pulp.chips.archytas.hierarchical_cache import Hierarchical_cache

from pulp.chips.archytas.archytas_arch import ArchytasArch
from pulp.chips.archytas.archytas_core import CV32CoreTest
# TODO: add and use AIMC accelerator
from pulp.idma.snitch_dma import SnitchDma
from pulp.xif_decoder.xif_decoder import XifDecoder
from pulp.magia_idma_ctrl.magia_idma_ctrl import Magia_iDMA_Ctrl


# adapted from snitch cluster model
# interface i_INPUT -> interleaver -> banks
class Archytas_A_TileTcdm(gvsoc.systree.Component):
    def __init__(self, parent, name, parser):
        super().__init__(parent, name)

        # TODO: Build a tile like the fixed T and then map the AIMC module
