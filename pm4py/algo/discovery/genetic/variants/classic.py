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
# Author: Maximilian Josef Frank (https://orcid.org/0000-0002-0714-7748)

from collections import defaultdict
import copy
import csv
from datetime import datetime
import numpy
import random
import itertools

# optional dependencies
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(iterable=None, *args, **kwargs):
        return iterable if iterable is not None else []

import pm4py
from pm4py.util import exec_utils, constants
from pm4py.util import xes_constants as xes
from pm4py.utils import is_polars_lazyframe
from pm4py.algo.discovery.genetic.algorithm import Parameters
from pm4py.objects.conversion.log import converter as log_converter
from pm4py.objects.conversion.genetic_matrix.variants.to_petri_net import apply as matrix2petrinet
from pm4py.algo.discovery.genetic.util import add_singleton_partition, get_src_sink_sets_for_wfnet, iset, rand_partition, remove_transition_from_partitions
from pm4py.objects.genetic_matrix.obj import GeneticMatrix

# typing
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
from pandas.core.frame import DataFrame
from pm4py.objects.log.obj import EventLog, EventStream
from pm4py.objects.petri_net.obj import PetriNet, Marking
from pm4py.algo.discovery.genetic.util import TransitionMap, InputMap, OutputMap, Individual


def apply(
    log: Union[EventLog, EventStream, DataFrame],
    parameters: Optional[Dict[Union[str, Parameters], Any]] = None,
) -> Tuple[PetriNet, Marking, Marking]:
    """
    Discovers a Petri net using Genetic Miner

    Reference paper:
    Maximilian Josef Frank. "Optimising and Implementing the Genetic Miner in PM4Py" (2026).

    Parameters
    ------------
    log
        Event log
    parameters
        Possible parameters of the algorithm,
        including:

            - Parameters.ACTIVITY_KEY
            - Parameters.TIMESTAMP_KEY
            - Parameters.CASE_ID_KEY
            - Parameters.POPULATION_SIZE
            - Parameters.ELITISM_RATE
            - Parameters.CROSSOVER_RATE
            - Parameters.MUTATION_RATE
            - Parameters.GENERATIONS
            - Parameters.ELITISM_MIN_SAMPLE
            - Parameters.LOG_CSV

    Returns
    ------------
    net
        Petri net
    im
        Initial marking
    fm
        Final marking
    """
    if parameters is None:
        parameters = {}
    if is_polars_lazyframe(log):
        log = log.collect().to_pandas()
    if not isinstance(log, DataFrame):
        log = log_converter.apply(
            log,
            variant=log_converter.Variants.TO_DATA_FRAME,
            parameters=parameters,
        )

    activity_key = exec_utils.get_param_value(
        Parameters.ACTIVITY_KEY, parameters, xes.DEFAULT_NAME_KEY
    )
    timestamp_key = exec_utils.get_param_value(
        Parameters.TIMESTAMP_KEY, parameters, xes.DEFAULT_TIMESTAMP_KEY
    )
    case_id_key = exec_utils.get_param_value(
        Parameters.CASE_ID_KEY, parameters, constants.CASE_CONCEPT_NAME
    )

    population_size = exec_utils.get_param_value(
        Parameters.POPULATION_SIZE, parameters, 500
    )
    elitism_rate = exec_utils.get_param_value(
        Parameters.ELITISM_RATE, parameters, 0.01
    )
    crossover_rate = exec_utils.get_param_value(
        Parameters.CROSSOVER_RATE, parameters, 1.0
    )
    mutation_rate = exec_utils.get_param_value(
        Parameters.MUTATION_RATE, parameters, 0.01
    )
    generations = exec_utils.get_param_value(
        Parameters.GENERATIONS, parameters, 100
    )
    elitism_min_sample = exec_utils.get_param_value(
        Parameters.ELITISM_MIN_SAMPLE, parameters, 5
    )
    log_csv = exec_utils.get_param_value(
        Parameters.LOG_CSV, parameters, None
    )

    # configure parameters
    if population_size < 2:
        raise ValueError("population_size < 2: You need at least two parents for each next generation, thus at least a population size of 2.")
    if elitism_min_sample >= population_size:
        elitism_min_sample = population_size - 1
    if elitism_min_sample < 1:
        raise ValueError("elitism_min_sample < 1: No empty samples allowed.")
    if log_csv:
        log_csv = csv.writer(log_csv)
        log_csv.writerow(['timestamp', 'generation'] + [f'fitness{i}' for i in range(population_size)])
    # @src 6.3. Genetic Operations; https://doi.org/10.1007/11494744_5
    T = tuple(log[activity_key].unique())
    history = []
    # initial population
    population = individuals(log, population_size, T, { # [(I,O), …]
        "activity_key":activity_key, "timestamp_key":timestamp_key, "case_id_key":case_id_key
    })
    population, fitness = tournament(tqdm(population, f"└─Tournament {len(history)}"), log, T, sort=True)
    if log_csv:
        log_csv.writerow([datetime.now(), len(history)] + fitness)
    # generations (generation-1 because initial population already generated)
    for _ in tqdm(range(generations-1), "Genetic generations"):
        if fitness[0] == 1 or (history and all(f == fitness[0] for f in history[-int(generations/2):])):
            break
        history.append(fitness[0])
        # elitism
        next_population = population[:round(elitism_rate * population_size)]
        # fill with offsprings
        while len(next_population) < population_size:
            parent1, parent2 = sample_parents(population, fitness, elitism_min_sample)
            if random.random() < crossover_rate:
                offsprings = crossover(parent1, parent2, T)
            else:
                offsprings = copy.deepcopy((parent1, parent2))
            for offspring in offsprings:
                if len(next_population) < population_size:
                    offspring = mutate(offspring, mutation_rate)
                    next_population.append(offspring)
        # sorts population by fitness
        population, fitness = tournament(tqdm(next_population, f"└─Tournament {len(history)}"), log, T, sort=True)
        if log_csv:
            log_csv.writerow([datetime.now(), len(history)] + fitness)
    return matrix2petrinet(GeneticMatrix(*population[0], T))

def individuals(log: Union[DataFrame, EventLog], sample_size=1, T=None, keys: Dict[str, str] = {"activity_key":xes.DEFAULT_NAME_KEY, "timestamp_key":xes.DEFAULT_TIMESTAMP_KEY, "case_id_key":constants.CASE_CONCEPT_NAME}) -> List[Individual]:
    if not T:
        T = tuple(log[keys['activity_key']].unique())
    # polyfill for itertools.pairwise (requires Python 3.10+)
    # @src https://docs.python.org/3/library/itertools.html#itertools.pairwise
    def pairwise(iterable):
        # pairwise('ABCDEFG') → AB BC CD DE EF FG
        iterator = iter(iterable)
        a = next(iterator, None)
        for b in iterator:
           yield a, b
           a = b
    # @src 6.1. Initial Population; https://doi.org/10.1007/11494744_5
    # create matrix C
    C = numpy.zeros((len(T), len(T)))
    for _,group in tqdm(log.sort_values(keys['timestamp_key'], ascending=True).groupby(keys['case_id_key']), desc="Find consecutive activities"):
        for row1,row2 in pairwise(map(lambda r: r[1], group.iterrows())):
            i = T.index(row1[keys['activity_key']])
            o = T.index(row2[keys['activity_key']])
            C[i,o] += 1
    Cn = numpy.nan_to_num(C / C.sum(axis=1)[:,None])    # normalise row-wise
    samples = []
    for _ in tqdm(range(sample_size), "Initial population"):
        I,O = defaultdict(list), defaultdict(list)
        for i,o in numpy.ndindex(C.shape):
            if random.random() < Cn[i,o]:    # [0,1[ < [0,1]; 0 < 0 = false
                O[T[i]].append(T[o])
                I[T[o]].append(T[i])
        I,O = repair(I, O, C, T)
        # partitioning already ensures no T in >1 partitions
        # see 4. Causal Matrix, Def. 4; https://doi.org/10.1007/11494744_5
        for i in I.keys():
            I[i] = rand_partition(I[i])
        for o in O.keys():
            O[o] = rand_partition(O[o])
        samples.append((I,O))
    return samples

def tournament(
    population: List[Individual],
    log: Union[DataFrame, EventLog],
    T,
    sort=True,
    activity_key: str = xes.DEFAULT_NAME_KEY,
    timestamp_key: str = xes.DEFAULT_TIMESTAMP_KEY,
    case_id_key: str = constants.CASE_CONCEPT_NAME,
) -> Tuple[List[Individual], List[float]]:
    """sort=True: sort descending by fitness (i.e. best first)"""
    # @src 6.2. Fitness Calculation; https://doi.org/10.1007/11494744_5
    fitness = []
    for i,(I,O) in enumerate(population):
        model = matrix2petrinet(GeneticMatrix(I,O,T))
        metrics = pm4py.fitness_token_based_replay(
            log,
            *model,
            activity_key=activity_key,
            timestamp_key=timestamp_key,
            case_id_key=case_id_key,
        )
        fitness.append(
            0.4 * metrics['average_trace_fitness']
            # @see https://pm4py-source.readthedocs.io/en/stable/_modules/pm4py/algo/evaluation/replay_fitness/variants/token_replay.html#evaluate
            # average_fitness = sum_fitness / #traces
            # = ∑ fitness per trace / #traces
            #   ∑ fitness per trace * len(log)/#traces
            # = ––––––––––––––––––––––––––––––––––––––
            #        #traces * len(log)/#traces
            #   ∑ fitness per row in log   ∑ fitness per activity
            # = –––––––––––––––––––––––– = ––––––––––––––––––––––
            #           len(log)                 len(log)
            +
            0.6 * metrics['percentage_of_fitting_traces']/100
        )
    if sort:
        population, fitness = zip(*sorted(
            zip(population, fitness),
            key=lambda obj: obj[1],
            reverse=True
        ))
        population, fitness = list(population), list(fitness)
    return (population, fitness)

def sample_parents(population: List[Individual], fitness: List[float], elitism_min_sample: int):
    remaining = list(range(len(population)))
    first_index = max(
        random.sample(remaining, k=elitism_min_sample), key=fitness.__getitem__
    )
    remaining.remove(first_index)
    parent1 = population[first_index]

    # Prefer a different structure, even when there are too few for a full tournament.
    distinct = [index for index in remaining if population[index] != parent1]
    candidates = distinct or remaining
    second_index = max(
        random.sample(candidates, k=min(elitism_min_sample, len(candidates))),
        key=fitness.__getitem__,
    )
    return parent1, population[second_index]

def crossover(parent1: Individual, parent2: Individual, T: List[str]) -> Tuple[Individual, Individual]:
    # @src 6.3. Genetic Operations: Crossover; https://doi.org/10.1007/11494744_5
    # 1. cross-over point
    t = random.choice(T)
    # 2. clone parents
    I1,O1 = offspring1 = copy.deepcopy(parent1)
    I2,O2 = offspring2 = copy.deepcopy(parent2)
    # 3. swap and recombine
    if I1[t] and I2[t]:
        swap_point = random.randrange(min(len(I1[t]), len(I2[t])))
        toI1, toI2 = I2[t][swap_point:], I1[t][swap_point:]
        # no T can exist twice in I/O[t], see Def. 4; https://doi.org/10.1007/11494744_5
        # COPY of I_i, else not properly removed in opposite I_j
        I1_flat = iset.flat(I1[t][:swap_point])
        toI1_dedup = [iset(S - I1_flat) for S in toI1 if S - I1_flat] # skips {}
        I2_flat = iset.flat(I2[t][:swap_point])
        toI2_dedup = [iset(S - I2_flat) for S in toI2 if S - I2_flat] # skips {}
        # merge
        old_I1 = iset.flat(I1[t])
        old_I2 = iset.flat(I2[t])
        I1[t], I2[t] = I1[t][:swap_point] + toI1_dedup, I2[t][:swap_point] + toI2_dedup
        # @src 6.3. Genetic Operations: Update Related Elements; https://doi.org/10.1007/11494744_5
        new_I1 = iset.flat(I1[t])
        new_I2 = iset.flat(I2[t])
        for c in new_I1 - old_I1:
            add_singleton_partition(O1, c, t)
        for c in old_I1 - new_I1:
            remove_transition_from_partitions(O1, c, t)
        for c in new_I2 - old_I2:
            add_singleton_partition(O2, c, t)
        for c in old_I2 - new_I2:
            remove_transition_from_partitions(O2, c, t)
    if O1[t] and O2[t]:
        swap_point = random.randrange(min(len(O1[t]), len(O2[t])))
        toO1, toO2 = O2[t][swap_point:], O1[t][swap_point:]
        # no T can exist twice in I/O[t], see Def. 4; https://doi.org/10.1007/11494744_5
        # COPY of I_i, else not properly removed in opposite I_j
        O1_flat = iset.flat(O1[t][:swap_point])
        toO1_dedup = [iset(S - O1_flat) for S in toO1 if S - O1_flat] # skips {}
        O2_flat = iset.flat(O2[t][:swap_point])
        toO2_dedup = [iset(S - O2_flat) for S in toO2 if S - O2_flat] # skips {}
        # merge
        old_O1 = iset.flat(O1[t])
        old_O2 = iset.flat(O2[t])
        O1[t], O2[t] = O1[t][:swap_point] + toO1_dedup, O2[t][:swap_point] + toO2_dedup
        # @src 6.3. Genetic Operations: Update Related Elements; https://doi.org/10.1007/11494744_5
        for c in iset.flat(O1[t]) - old_O1:
            add_singleton_partition(I1, c, t)
        for c in old_O1 - iset.flat(O1[t]):
            remove_transition_from_partitions(I1, c, t)
        for c in iset.flat(O2[t]) - old_O2:
            add_singleton_partition(I2, c, t)
        for c in old_O2 - iset.flat(O2[t]):
            remove_transition_from_partitions(I2, c, t)
    return (offspring1, offspring2) # = (I1,O1),(I2,O2) by reference

def mutate(individual: Individual, rate: float = 0.01) -> Individual:
    # @src 6.3. Genetic Operations: Mutation; https://doi.org/10.1007/11494744_5
    I,O = individual
    for t in I.keys():
        if random.random() < rate:
            I[t] = rand_partition(itertools.chain(*I[t]))
    for t in O.keys():
        if random.random() < rate:
            O[t] = rand_partition(itertools.chain(*O[t]))
    return (I,O)

def repair(I: InputMap, O: OutputMap, C: numpy.ndarray, T: List[str]) -> Individual:
    """
    Merging partitions until petri-net is (coherent) workflow net
    see last requirement in 4. Causal Matrix, Def. 4; https://doi.org/10.1007/11494744_5
    """
    # WF-Net Definition: each node on path from i to o
    #   → re-connect partitions of each I and O, not I and O together
    left = set(T)
    partitions = []
    while left:
        partition = set()
        Tn = {left.pop()}
        while Tn:
            t = Tn.pop() # also removes from Tn
            left.discard(t) # remove without Exception (see initial Tn)
            partition.add(t)
            Tn |= (set(I[t]) | set(O[t])) & left
        partitions.append(partition)
    T_idx = {t:i for i,t in enumerate(T)} # faster than T.index(t)
    
    def rand_connect_one(I: InputMap, O: OutputMap, Ti: Iterable[str], To: Iterable[str], C: numpy.ndarray) -> Individual:
        comb = tuple(itertools.product(Ti, To))
        try:
            ti,to = random.choices(
                comb,
                weights = [ C[T_idx[ti], T_idx[to]] for ti,to in comb ],
                k=1
            )[0]
        except ValueError:
            ti,to = random.choice(comb)
        O[ti].append(to)
        I[to].append(ti)
        return I,O
    
    while len(partitions) > 1:
        random.shuffle(partitions)
        # merge Ti / To of partition to other partition
        sources, sinks = get_src_sink_sets_for_wfnet(I, O, partitions[1])
        for i in sources:
            # connect any→i
            I,O = rand_connect_one(I, O, partitions[0], [i], C)
        for o in sinks:
            # connect o→any
            I,O = rand_connect_one(I, O, [o], partitions[0], C)
        # pop first + merge with new first (i.e. old second)
        merging = partitions.pop(0)
        partitions[0] |= merging
    return (I,O)
