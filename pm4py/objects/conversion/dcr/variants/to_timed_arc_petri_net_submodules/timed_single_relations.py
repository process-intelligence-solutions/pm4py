from pm4py.objects.petri_net.obj import *

from pm4py.objects.conversion.dcr.variants.to_timed_arc_petri_net_submodules import timed_utils

class TimedSingleRelations(object):

    def __init__(self, helper_struct, mapping_exceptions) -> None:
        self.helper_struct = helper_struct
        self.mapping_exceptions = mapping_exceptions

    def create_include_pattern(self, event, event_prime, tapn) -> PetriNet:
        inc_place_e_prime = self.helper_struct[event_prime]['places']['included']
        pend_places_e_prime = self.helper_struct[event_prime]['places']['pending']
        pend_excl_places_e_prime = self.helper_struct[event_prime]['places']['pending_excluded']
        copy_0 = self.helper_struct[event]['transitions']
        len_copy_0 = len(copy_0)
        len_internal = self.helper_struct[event]['len_internal']
        len_delta = int(len_copy_0 / len_internal)
        new_transitions = []

        # copy 1
        if inc_place_e_prime and len(pend_places_e_prime) > 0 and len(pend_excl_places_e_prime) > 0:
            for _, (pend_place_e_prime, pend_excl_place_e_prime) in self.helper_struct[event_prime]['pending_pairs'].items():
                for delta in range(len_delta):
                    # (exists) for each event create a transition with a transport arc link (independent of the other pending places)
                    tapn, ts = timed_utils.create_event_pattern_transitions_and_arcs(tapn, event, self.helper_struct, self.mapping_exceptions)
                    new_transitions.extend(ts)
                    for t in ts:
                        tapn, t = timed_utils.map_existing_transitions_of_copy_0(delta*len_internal, copy_0, t, tapn)
                        timed_utils.add_arc_from_to_with_check(t, inc_place_e_prime, tapn)
                        # timed_utils.add_arc_from_to(inc_place_e_prime, t, tapn, type='inhibitor')

                        pex_to_t = timed_utils.add_arc_from_to_with_check(pend_excl_place_e_prime, t, tapn, type='transport')
                        t_to_p = timed_utils.add_arc_from_to_with_check(t, pend_place_e_prime, tapn, type='transport')
                        pex_to_t.properties['transportindex'] = self.helper_struct['transport_index']
                        t_to_p.properties['transportindex'] = self.helper_struct['transport_index']
                        self.helper_struct['transport_index'] = self.helper_struct['transport_index'] + 1
        # copy 2
        if inc_place_e_prime:
            for delta in range(len_delta):
                tapn, ts = timed_utils.create_event_pattern_transitions_and_arcs(tapn, event, self.helper_struct, self.mapping_exceptions)
                new_transitions.extend(ts)
                for t in ts:
                    tapn, t = timed_utils.map_existing_transitions_of_copy_0(delta*len_internal, copy_0, t, tapn)
                    timed_utils.add_arc_from_to_with_check(t, inc_place_e_prime, tapn)
                    # timed_utils.add_arc_from_to(inc_place_e_prime, t, tapn, type='inhibitor')
                    # (for all) inhibitor arcs to all pending excluded places
                    for pend_excl_place_e_prime, _ in pend_excl_places_e_prime:
                        timed_utils.add_arc_from_to_with_check(pend_excl_place_e_prime, t, tapn, type='inhibitor')

        # map the copy_0 last but before adding the new transitions
        # copy 0
        if inc_place_e_prime:
            for t in copy_0:
                timed_utils.add_arc_from_to_with_check(t, inc_place_e_prime, tapn)
                timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn)

        self.helper_struct[event]['transitions'].extend(new_transitions)
        return tapn

    def create_exclude_pattern(self, event, event_prime, tapn) -> PetriNet:
        inc_place_e_prime = self.helper_struct[event_prime]['places']['included']
        pend_places_e_prime = self.helper_struct[event_prime]['places']['pending']
        pend_excl_places_e_prime = self.helper_struct[event_prime]['places']['pending_excluded']
        copy_0 = self.helper_struct[event]['transitions']
        len_copy_0 = len(copy_0)
        len_internal = self.helper_struct[event]['len_internal']
        len_delta = int(len_copy_0 / len_internal)
        new_transitions = []

        # copy 1
        if inc_place_e_prime:
            for delta in range(len_delta):
                tapn, ts = timed_utils.create_event_pattern_transitions_and_arcs(tapn, event, self.helper_struct, self.mapping_exceptions)
                new_transitions.extend(ts)
                for t in ts:
                    tapn, t = timed_utils.map_existing_transitions_of_copy_0(delta*len_internal, copy_0, t, tapn)
                    timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn)
                    #(for all) no pending event executes this transition
                    for pend_place_e_prime, _ in pend_places_e_prime:
                        timed_utils.add_arc_from_to_with_check(pend_place_e_prime, t, tapn, type='inhibitor')

        # copy 2
        if inc_place_e_prime and len(pend_places_e_prime) > 0 and len(pend_excl_places_e_prime) > 0:
            for _, (pend_place_e_prime, pend_excl_place_e_prime) in self.helper_struct[event_prime]['pending_pairs'].items():
                for delta in range(len_delta):
                    # (for each) pairwise transport arcs for each pair of pending places
                    tapn, ts = timed_utils.create_event_pattern_transitions_and_arcs(tapn, event, self.helper_struct, self.mapping_exceptions)
                    new_transitions.extend(ts)
                    for t in ts:
                        tapn, t = timed_utils.map_existing_transitions_of_copy_0(delta*len_internal, copy_0, t, tapn)
                        timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn)

                        p_to_t = timed_utils.add_arc_from_to_with_check(pend_place_e_prime, t, tapn, type='transport')
                        t_to_pex = timed_utils.add_arc_from_to_with_check(t, pend_excl_place_e_prime, tapn, type='transport')
                        p_to_t.properties['transportindex'] = self.helper_struct['transport_index']
                        t_to_pex.properties['transportindex'] = self.helper_struct['transport_index']
                        self.helper_struct['transport_index'] = self.helper_struct['transport_index'] + 1

        # copy 0
        if inc_place_e_prime:
            for t in copy_0:
                timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn, type='inhibitor')

        self.helper_struct[event]['transitions'].extend(new_transitions)
        return tapn

    def create_response_pattern(self, event, event_prime, tapn) -> PetriNet:
        inc_place_e_prime = self.helper_struct[event_prime]['places']['included']
        pend_place_e_prime = self.helper_struct['pend_matrix'][event_prime][event]
        pend_excl_place_e_prime = self.helper_struct['pend_exc_matrix'][event_prime][event]
        copy_0 = self.helper_struct[event]['transitions']
        len_copy_0 = len(copy_0)
        len_internal = self.helper_struct[event]['len_internal']
        len_delta = int(len_copy_0 / len_internal)
        new_transitions = []

        pend_places_e_prime = self.helper_struct[event_prime]['places']['pending']
        pend_excl_places_e_prime = self.helper_struct[event_prime]['places']['pending_excluded']
        pending_others = [x[0] for x in pend_places_e_prime if x[1] != event]
        pending_exc_others = [x[0] for x in pend_excl_places_e_prime if x[1] != event]
        # copy 1
        if len(pend_places_e_prime) > 0:# and self.helper_struct[event]['firstResp']:
            for delta in range(len_delta):
                tapn, ts = timed_utils.create_event_pattern_transitions_and_arcs(tapn, event, self.helper_struct, self.mapping_exceptions)
                new_transitions.extend(ts)
                for t in ts:
                    tapn, t = timed_utils.map_existing_transitions_of_copy_0(delta*len_internal, copy_0, t, tapn)
                    timed_utils.add_arc_from_to_with_check(t, inc_place_e_prime, tapn)
                    timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn)

                    timed_utils.add_arc_from_to_with_check(t, pend_place_e_prime, tapn)
                    timed_utils.add_arc_from_to_with_check(pend_place_e_prime, t, tapn, type='inhibitor')
                    for pend_other in pending_others:
                        # timed_utils.add_arc_from_to(t, pend_other, tapn)
                        timed_utils.add_arc_from_to_with_check(pend_other, t, tapn, type='inhibitor')
                    # timed_utils.add_arc_from_to(t, inc_place_e_prime, tapn)
                    # timed_utils.add_arc_from_to(inc_place_e_prime, t, tapn)
                    #
                    # timed_utils.add_arc_from_to(t, pend_place_e_prime, tapn)
                    # timed_utils.add_arc_from_to(pend_place_e_prime, t, tapn)
                    #
                    # # for pend_other in pending_others:
                    # #     timed_utils.add_arc_from_to(pend_other, t, tapn, type='inhibitor')

        # copy 2
        if inc_place_e_prime and len(pend_excl_places_e_prime) > 0:
            #if self.helper_struct[event]['firstResp']:
            for delta in range(len_delta):
                tapn, ts = timed_utils.create_event_pattern_transitions_and_arcs(tapn, event, self.helper_struct, self.mapping_exceptions)
                new_transitions.extend(ts)
                for t in ts:
                    tapn, t = timed_utils.map_existing_transitions_of_copy_0(delta*len_internal, copy_0, t, tapn)

                    timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn, type='inhibitor')

                    timed_utils.add_arc_from_to_with_check(t, pend_excl_place_e_prime, tapn)
                    timed_utils.add_arc_from_to_with_check(pend_excl_place_e_prime, t, tapn, type='inhibitor')
                    for pend_exc_other in pending_exc_others:
                        # timed_utils.add_arc_from_to(t, pend_exc_other, tapn)
                        timed_utils.add_arc_from_to_with_check(pend_exc_other, t, tapn, type='inhibitor')
            # copy 2X
            for pend_exc_other in pending_exc_others:
                for delta in range(len_delta):
                    tapn, ts = timed_utils.create_event_pattern_transitions_and_arcs(tapn, event, self.helper_struct, self.mapping_exceptions)
                    new_transitions.extend(ts)
                    for t in ts:
                        tapn, t = timed_utils.map_existing_transitions_of_copy_0(delta*len_internal, copy_0, t, tapn)
                        timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn, type='inhibitor')

                        timed_utils.add_arc_from_to_with_check(t, pend_excl_place_e_prime, tapn)
                        # timed_utils.add_arc_from_to(pend_excl_place_e_prime, t, tapn, type='inhibitor')

                        timed_utils.add_arc_from_to_with_check(pend_exc_other, t, tapn)

        # copy 3
        if inc_place_e_prime and len(pend_excl_places_e_prime) > 0:
            for delta in range(len_delta):
                tapn, ts = timed_utils.create_event_pattern_transitions_and_arcs(tapn, event, self.helper_struct, self.mapping_exceptions)
                new_transitions.extend(ts)
                for t in ts:
                    tapn, t = timed_utils.map_existing_transitions_of_copy_0(delta*len_internal, copy_0, t, tapn)
                    timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn, type='inhibitor')

                    timed_utils.add_arc_from_to_with_check(t, pend_excl_place_e_prime, tapn)
                    timed_utils.add_arc_from_to_with_check(pend_excl_place_e_prime, t, tapn)
                    # for pend_exc_other in pending_exc_others:
                    #     timed_utils.add_arc_from_to(pend_exc_other,t,tapn,type='inhibitor')

        # copy 0
        if len(pend_places_e_prime) > 0:
            # copy 0X
            for pend_other in pending_others:
                for delta in range(len_delta):
                    tapn, ts = timed_utils.create_event_pattern_transitions_and_arcs(tapn, event, self.helper_struct, self.mapping_exceptions)
                    new_transitions.extend(ts)
                    for t in ts:
                        tapn, t = timed_utils.map_existing_transitions_of_copy_0(delta * len_internal, copy_0, t, tapn)
                        timed_utils.add_arc_from_to_with_check(t, inc_place_e_prime, tapn)
                        timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn)

                        timed_utils.add_arc_from_to_with_check(t, pend_place_e_prime, tapn)
                        # TODO: check if I was right in removing this
                        # timed_utils.add_arc_from_to(pend_place_e_prime, t, tapn, type='inhibitor')

                        timed_utils.add_arc_from_to_with_check(pend_other, t, tapn)
            for t in copy_0:
                timed_utils.add_arc_from_to_with_check(t, inc_place_e_prime, tapn)
                timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn)

                timed_utils.add_arc_from_to_with_check(t, pend_place_e_prime, tapn)
                timed_utils.add_arc_from_to_with_check(pend_place_e_prime, t, tapn)

                # timed_utils.add_arc_from_to(t, inc_place_e_prime, tapn)
                # timed_utils.add_arc_from_to(inc_place_e_prime, t, tapn)
                #
                # timed_utils.add_arc_from_to(t, pend_place_e_prime, tapn)
                # timed_utils.add_arc_from_to(pend_place_e_prime, t, tapn, type='inhibitor')
                # for pend_other in pending_others:
                #     timed_utils.add_arc_from_to(t, pend_other, tapn)
                #     timed_utils.add_arc_from_to(pend_other, t, tapn, type='inhibitor')

        # self.helper_struct[event]['firstResp'] = False
        # when here I ask: have I done the first response?
        # If the answer is yes. Then
        # Do not create a new transition (do not copy any past behaviour)
        # Simply retrieve the transition that behaves towards the other place in that way and
        # add the same behaviour towards this transition
        # this applies the same way to a response or a no-response
        self.helper_struct[event]['transitions'].extend(new_transitions)
        return tapn

    def create_no_response_pattern(self, event, event_prime, tapn) -> PetriNet:
        inc_place_e_prime = self.helper_struct[event_prime]['places']['included']
        pend_places_e_prime = self.helper_struct[event_prime]['places']['pending']
        pend_excl_places_e_prime = self.helper_struct[event_prime]['places']['pending_excluded']
        copy_0 = self.helper_struct[event]['transitions']
        len_copy_0 = len(copy_0)
        len_internal = self.helper_struct[event]['len_internal']
        len_delta = int(len_copy_0 / len_internal)
        new_transitions = []

        # pend_place_e_prime = self.helper_struct['pend_matrix'][event_prime][event]
        # pending_others = [x[0] for x in pend_places_e_prime if x[1] != event]
        # copy 1
        if len(pend_places_e_prime) > 0:# and self.helper_struct[event]['firstResp']:
            # (for all) if included and not pending then fire
            # for delta in range(len_delta):
            #     tapn, ts = timed_utils.create_event_pattern_transitions_and_arcs(tapn, event, self.helper_struct, self.mapping_exceptions)
            #     new_transitions.extend(ts)
            #     for t in ts:
            #         tapn, t = timed_utils.map_existing_transitions_of_copy_0(delta*len_internal, copy_0, t, tapn)
            #         timed_utils.add_arc_from_to(t, inc_place_e_prime, tapn)
            #         timed_utils.add_arc_from_to(inc_place_e_prime, t, tapn)
            #         for pp_e_prime, _ in pend_places_e_prime:
            #             timed_utils.add_arc_from_to(pp_e_prime, t, tapn, type='inhibitor')

            for pp_e_prime,_ in pend_places_e_prime:
                for delta in range(len_delta):
                    tapn, ts = timed_utils.create_event_pattern_transitions_and_arcs(tapn, event, self.helper_struct, self.mapping_exceptions)
                    new_transitions.extend(ts)
                    for t in ts:
                        tapn, t = timed_utils.map_existing_transitions_of_copy_0(delta*len_internal, copy_0, t, tapn)
                        timed_utils.add_arc_from_to_with_check(t, inc_place_e_prime, tapn)
                        timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn)

                        timed_utils.add_arc_from_to_with_check(pp_e_prime, t, tapn)
        # copy 2
        if inc_place_e_prime and len(pend_excl_places_e_prime) > 0:# and self.helper_struct[event]['firstNoResp']:
            # (for all) if no pending excl place is pending and not included then it fires
            for delta in range(len_delta):
                tapn, ts = timed_utils.create_event_pattern_transitions_and_arcs(tapn, event, self.helper_struct, self.mapping_exceptions)
                new_transitions.extend(ts)
                for t in ts:
                    tapn, t = timed_utils.map_existing_transitions_of_copy_0(delta*len_internal, copy_0, t, tapn)
                    timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn, type='inhibitor')
                    for pend_excl_place_e_prime, _ in pend_excl_places_e_prime:
                        timed_utils.add_arc_from_to_with_check(pend_excl_place_e_prime, t, tapn, type='inhibitor')

        # copy 3
        if inc_place_e_prime and len(pend_excl_places_e_prime) > 0:
            # (exists) for each pending excluded place if it is pending make it unpending when event is not included
            for pend_excl_place_e_prime, _ in pend_excl_places_e_prime:
                for delta in range(len_delta):
                    tapn, ts = timed_utils.create_event_pattern_transitions_and_arcs(tapn, event, self.helper_struct, self.mapping_exceptions)
                    new_transitions.extend(ts)
                    for t in ts:
                        tapn, t = timed_utils.map_existing_transitions_of_copy_0(delta*len_internal, copy_0, t, tapn)
                        timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn, type='inhibitor')

                        timed_utils.add_arc_from_to_with_check(pend_excl_place_e_prime, t, tapn)

        # copy 0
        if len(pend_places_e_prime) > 0:
            # (exists) for each pending incl place we need to make the specific place unpending and inhibitor arcs to the rest
            # for pend_other in pending_others:
            #     for delta in range(len_delta):
            #         tapn, ts = timed_utils.create_event_pattern_transitions_and_arcs(tapn, event, self.helper_struct, self.mapping_exceptions)
            #         new_transitions.extend(ts)
            #         for t in ts:
            #             tapn, t = timed_utils.map_existing_transitions_of_copy_0(delta * len_internal, copy_0, t, tapn)
            #             timed_utils.add_arc_from_to(t, inc_place_e_prime, tapn)
            #             timed_utils.add_arc_from_to(inc_place_e_prime, t, tapn)
            #
            #             timed_utils.add_arc_from_to(pend_other, t, tapn)
            for t in copy_0:
                # timed_utils.add_arc_from_to(t, inc_place_e_prime, tapn)
                # timed_utils.add_arc_from_to(inc_place_e_prime, t, tapn)
                #
                # timed_utils.add_arc_from_to(pend_place_e_prime, t, tapn)

                timed_utils.add_arc_from_to_with_check(t, inc_place_e_prime, tapn)
                timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn)
                for pp_e_prime, _ in pend_places_e_prime:
                    timed_utils.add_arc_from_to_with_check(pp_e_prime, t, tapn, type='inhibitor')

        # self.helper_struct[event]['firstResp'] = False
        self.helper_struct[event]['transitions'].extend(new_transitions)
        return tapn

    def create_condition_pattern(self, event, event_prime, tapn, delay=0) -> PetriNet:
        inc_place_e_prime = self.helper_struct[event_prime]['places']['included']
        exec_place_e_prime = self.helper_struct[event_prime]['places']['executed']

        copy_0 = self.helper_struct[event]['transitions']
        len_copy_0 = len(copy_0)
        len_internal = self.helper_struct[event]['len_internal']
        len_delta = int(len_copy_0 / len_internal)
        new_transitions = []
        # copy 1
        if inc_place_e_prime and exec_place_e_prime:
            for delta in range(len_delta):
                tapn, ts = timed_utils.create_event_pattern_transitions_and_arcs(tapn, event, self.helper_struct, self.mapping_exceptions)
                new_transitions.extend(ts)
                for t in ts:
                    tapn, t = timed_utils.map_existing_transitions_of_copy_0(delta*len_internal, copy_0, t, tapn)
                    timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn, type='inhibitor')

        # copy 0
        if exec_place_e_prime:
            for t in copy_0:
                timed_utils.add_arc_from_to_with_check(t, inc_place_e_prime, tapn)
                timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn)

                t_to_p = timed_utils.add_arc_from_to_with_check(t, exec_place_e_prime, tapn, type='transport')
                p_to_t = timed_utils.add_arc_from_to_with_check(exec_place_e_prime, t, tapn, type='transport')
                t_to_p.properties['transportindex'] = self.helper_struct['transport_index']
                p_to_t.properties['transportindex'] = self.helper_struct['transport_index']
                self.helper_struct['transport_index'] = self.helper_struct['transport_index'] + 1
                if delay and delay > 0:
                    p_to_t.properties['agemin'] = delay

        self.helper_struct[event]['transitions'].extend(new_transitions)
        return tapn

    def create_milestone_pattern(self, event, event_prime, tapn) -> PetriNet:
        inc_place_e_prime = self.helper_struct[event_prime]['places']['included']
        pend_places_e_prime = self.helper_struct[event_prime]['places']['pending']
        # pend_excluded_places_e_prime = self.helper_struct[event_prime]['places']['pending_excluded']

        copy_0 = self.helper_struct[event]['transitions']
        len_copy_0 = len(copy_0)
        len_internal = self.helper_struct[event]['len_internal']
        len_delta = int(len_copy_0 / len_internal)
        new_transitions = []
        # copy 1
        if inc_place_e_prime:
            for delta in range(len_delta):
                tapn, ts = timed_utils.create_event_pattern_transitions_and_arcs(tapn, event, self.helper_struct, self.mapping_exceptions)
                new_transitions.extend(ts)
                for t in ts:
                    tapn, t = timed_utils.map_existing_transitions_of_copy_0(delta*len_internal, copy_0, t, tapn)

                    timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn, type='inhibitor')

        # copy 0
        if len(pend_places_e_prime) > 0:
            for t in copy_0:
                timed_utils.add_arc_from_to_with_check(t, inc_place_e_prime, tapn)
                timed_utils.add_arc_from_to_with_check(inc_place_e_prime, t, tapn)

                for pend_place_e_prime,_ in pend_places_e_prime:
                    timed_utils.add_arc_from_to_with_check(pend_place_e_prime, t, tapn, type='inhibitor')

        self.helper_struct[event]['transitions'].extend(new_transitions)
        return tapn
