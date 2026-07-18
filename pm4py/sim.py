'''
PM4Py – A Process Mining Library for Python
Copyright (C) 2026 Process Intelligence Solutions GmbH

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as
published by the Free Software Foundation, either version 3 of the
License, or any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see this software project's root or
visit <https://www.gnu.org/licenses/>.

Website: https://processintelligence.solutions
Contact: info@processintelligence.solutions
'''
__doc__ = """
The ``pm4py.sim`` module contains simulation algorithms provided by ``pm4py``.
"""

from collections import Counter
from typing import Union, Tuple

from pm4py.objects.log.obj import EventLog
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.objects.process_tree.obj import ProcessTree


def play_out(
    *args: Union[
        Tuple[PetriNet, Marking, Marking], dict, Counter, ProcessTree
    ],
    **kwargs
) -> EventLog:
    """
    Performs the playout of the provided model, generating a set of traces.

    The function accepts one of the following inputs:

    - A Petri net with initial and final markings.
    - A Directly-Follows Graph (DFG) represented as a dictionary.
    - A process tree.

    :param args:

        - For Petri net playout: a `PetriNet`, an initial `Marking`, and a final `Marking`.
        - For DFG playout: a `dict` representing the DFG, followed by additional required arguments.
        - For process tree playout: a single `ProcessTree`. :param kwargs: Optional parameters of the method, including:
        - `parameters`: A dictionary containing parameters of the playout, such as:
            - `smap`: (optional) A stochastic map to be used for probabilistic transition selection.
            - `log`: (optional) An `EventLog` used to compute the stochastic map if `smap` is not provided.

    :rtype: ``EventLog``

    .. code-block:: python3

        import pm4py

        net, im, fm = pm4py.read_pnml('model.pnml')
        log = pm4py.play_out(net, im, fm)

    """
    if len(args) == 3:
        from pm4py.objects.petri_net.obj import PetriNet

        if isinstance(args[0], PetriNet):
            from pm4py.objects.petri_net.obj import ResetNet, InhibitorNet
            from pm4py.algo.simulation.playout.petri_net import algorithm
            from pm4py.objects.petri_net.semantics import ClassicSemantics
            from pm4py.objects.petri_net.inhibitor_reset.semantics import (
                InhibitorResetSemantics,
            )

            net = args[0]
            im = args[1]
            fm = args[2]
            parameters = (
                kwargs["parameters"] if "parameters" in kwargs else None
            )
            if parameters is None:
                parameters = {}

            variant = algorithm.Variants.BASIC_PLAYOUT
            # if the log, or the stochastic map of the transitions, is provided
            # use the stochastic playout in place of the basic playout
            # (that means, the relative weight of the transitions in a marking
            # will be considered during transition's picking)
            if "log" in parameters or "smap" in parameters:
                variant = algorithm.Variants.STOCHASTIC_PLAYOUT

            semantics = ClassicSemantics()
            if isinstance(net, ResetNet) or isinstance(net, InhibitorNet):
                semantics = InhibitorResetSemantics()
            parameters["petri_semantics"] = semantics

            return algorithm.apply(
                net,
                im,
                final_marking=fm,
                variant=variant,
                parameters=parameters,
            )
        elif isinstance(args[0], dict):
            from pm4py.algo.simulation.playout.dfg import (
                algorithm as dfg_playout,
            )

            return dfg_playout.apply(args[0], args[1], args[2], **kwargs)
    elif len(args) == 1:
        from pm4py.objects.process_tree.obj import ProcessTree, EnhancedProcessTree

        if isinstance(args[0], EnhancedProcessTree):
            from pm4py import convert_to_petri_net
            net, im , fm = convert_to_petri_net(args[0])
            return play_out(net, im, fm, **kwargs)

        if isinstance(args[0], ProcessTree):
            from pm4py.algo.simulation.playout.process_tree import algorithm

            return algorithm.apply(args[0], **kwargs)
        elif isinstance(args[0], dict):
            if "precedence" in args[0]:
                from pm4py.algo.simulation.playout.declare import algorithm

                return algorithm.apply(args[0], **kwargs)

    raise Exception("Unsupported model for playout")


def generate_process_tree(**kwargs) -> ProcessTree:
    """
    Generates a process tree.

    Reference paper:
    PTandLogGenerator: A Generator for Artificial Event Data

    :param kwargs: Parameters for the process tree generator algorithm.
    :rtype: ``ProcessTree``

    .. code-block:: python3

        import pm4py

        process_tree = pm4py.generate_process_tree()
    """
    from pm4py.algo.simulation.tree_generator import algorithm

    return algorithm.apply(**kwargs)
