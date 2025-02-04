# Log-Model Evaluation

In PM4Py, it is possible to compare the behavior contained in the log and the behavior contained in the model to see if and how they match. Four different dimensions exist in process mining: replay fitness, precision, generalization, and simplicity.

## Replay Fitness

The calculation of replay fitness aims to determine how much of the behavior in the log is admitted by the process model. We propose two methods to calculate replay fitness, based on token-based replay and alignments, respectively.

For token-based replay, the percentage of completely fitting traces is returned, along with a fitness value calculated as indicated in the scientific contribution:
Berti, Alessandro, and Wil MP van der Aalst. "Reviving Token-based Replay: Increasing Speed While Improving Diagnostics." ATAED@ Petri Nets/ACSD. 2019.

For alignments, the percentage of completely fitting traces is returned, along with a fitness value calculated as the average of the fitness values of the individual traces. The two variants of replay fitness are implemented as `Variants.TOKEN_BASED` and `Variants.ALIGNMENT_BASED` respectively.

To calculate the replay fitness between an event log and a Petri net model using the token-based replay method, use the code on the right side. The resulting value is a number between `0` and `1`.

```python
import pm4py

if __name__ == "__main__":
    fitness = pm4py.fitness_token_based_replay(log, net, im, fm)
```

To calculate the replay fitness between an event log and a Petri net model using the alignments method, use the code on the right side. The resulting value is a number between `0` and `1`.

```python
import pm4py

if __name__ == "__main__":
    fitness = pm4py.fitness_alignments(log, net, im, fm)
```

## Precision

We propose two approaches for measuring precision in PM4Py:

- **ETConformance** (using token-based replay): The reference paper is

  Muñoz-Gama, Jorge, and Josep Carmona. "A fresh look at precision in process conformance." International Conference on Business Process Management. Springer, Berlin, Heidelberg, 2010.

- **Align-ETConformance** (using alignments): The reference paper is

  Adriansyah, Arya, et al. "Measuring precision of modeled behavior." Information Systems and e-Business Management 13.1 (2015): 37-67.

The underlying idea of both approaches is the same: different prefixes of the log are replayed (when possible) on the model. At the reached marking, the set of transitions enabled in the process model is compared with the set of activities that follow the prefix. The more the sets differ, the lower the precision value; the more the sets are similar, the higher the precision value. This works only if the replay of the prefix on the process model succeeds; if the replay does not produce a result, the prefix is not considered for the computation of precision. Hence, precision calculated on top of unfit processes is not meaningful.

The main difference between the approaches is the replay method. Token-based replay is faster but based on heuristics (hence the replay result might not be exact). Alignments are exact, work on any kind of relaxed sound nets, but can be slow if the state space is large.

The two variants, ETConformance and Align-ETConformance, are available as `Variants.ETCONFORMANCE_TOKEN` and `Variants.ALIGN_ETCONFORMANCE` in the implementation, respectively.

To calculate the precision between an event log and a Petri net model using the ETConformance method, use the code on the right side. The resulting value is a number between `0` and `1`.

```python
import pm4py

if __name__ == "__main__":
    prec = pm4py.precision_token_based_replay(log, net, im, fm)
```

To calculate the precision between an event log and a Petri net model using the Align-ETConformance method, use the code on the right side. The resulting value is a number between `0` and `1`.

```python
import pm4py

if __name__ == "__main__":
    prec = pm4py.precision_alignments(log, net, im, fm)
```

## Generalization

Generalization is the third dimension to analyze how the log and the process model match. In particular, we propose the generalization measure described in the following research paper:
Buijs, Joos CAM, Boudewijn F. van Dongen, and Wil MP van der Aalst. "Quality dimensions in process discovery: The importance of fitness, precision, generalization, and simplicity." International Journal of Cooperative Information Systems 23.01 (2014): 1440001.

Basically, a model is considered general if the elements of the model are visited frequently enough during a replay operation (of the log on the model). A model may perfectly fit the log and be perfectly precise (for example, reporting the traces of the log as sequential models going from the initial marking to the final marking; a choice is operated at the initial marking). Hence, to measure generalization, a token-based replay operation is performed, and generalization is calculated as

$$ 1 - \text{avg}_t (\sqrt{1.0 / \text{freq}(t)}) $$

where $\text{avg}_t$ is the average of the inner value over all the transitions, $\sqrt{}$ is the square root, and $\text{freq}(t)$ is the frequency of $t$ after the replay.

To calculate the generalization between an event log and a Petri net model using the generalization method proposed in this section, use the code on the right side. The resulting value is a number between `0` and `1`.

```python
from pm4py.algo.evaluation.generalization import algorithm as generalization_evaluator

if __name__ == "__main__":
    gen = generalization_evaluator.apply(log, net, im, fm)
```

## Simplicity

Simplicity is the fourth dimension to analyze a process model. In this case, we define simplicity by considering only the Petri net model. The criterion we use for simplicity is the inverse arc degree, as described in the following research paper:
Blum, Fabian Rojas. "Metrics in process discovery." Technical Report TR/DCC-2015-6, Computer Science Department, University of Chile, 2015.

First, we consider the average degree for a place/transition of the Petri net, defined as the sum of the number of input arcs and output arcs. If all the places have at least one input arc and one output arc, the number is at least 2. Choosing a number $k$ between 0 and infinity, simplicity based on the inverse arc degree is defined as

$$ 1.0 / (1.0 + \max(\mathrm{mean\_deg} - k, 0)) $$

To calculate the simplicity of a Petri net model using the inverse arc degree, use the following code. The resulting value is a number between `0` and `1`.

```python
from pm4py.algo.evaluation.simplicity import algorithm as simplicity_evaluator

if __name__ == "__main__":
    simp = simplicity_evaluator.apply(net)
```

## Earth Mover Distance

The Earth Mover Distance, introduced in:
Leemans, Sander JJ, Anja F. Syring, and Wil MP van der Aalst. “Earth movers’ stochastic conformance checking.” International Conference on Business Process Management. Springer, Cham, 2019.
provides a way to calculate the distance between two different stochastic languages. Generally, one language is extracted from the event log, and one language is extracted from the process model. By language, we mean a set of traces weighted according to their probability.

For the event log, taking the set of variants of the log and dividing by the total number of traces provides the language of the log. We can see how the language of the model can be discovered by importing an event log and calculating its language:

```python
import pm4py
from pm4py.statistics.variants.log import get as variants_module

if __name__ == "__main__":
    log = pm4py.read_xes("tests/input_data/running-example.xes")
    log = pm4py.convert_to_event_log(log)
    language = variants_module.get_language(log)
    print(language)
```

Obtaining the following probability distribution:
{('register request', 'examine casually', 'check ticket', 'decide', 'reinitiate request', 'examine thoroughly', 'check ticket', 'decide', 'pay compensation'): 0.16666666666666666,
('register request', 'check ticket', 'examine casually', 'decide', 'pay compensation'): 0.16666666666666666,
('register request', 'examine thoroughly', 'check ticket', 'decide', 'reject request'): 0.16666666666666666,
('register request', 'examine casually', 'check ticket', 'decide', 'pay compensation'): 0.16666666666666666,
('register request', 'examine casually', 'check ticket', 'decide', 'reinitiate request', 'check ticket', 'examine casually', 'decide', 'reinitiate request', 'examine casually', 'check ticket', 'decide', 'reject request'): 0.16666666666666666,
('register request', 'check ticket', 'examine thoroughly', 'decide', 'reject request'): 0.16666666666666666}

The same does not naturally occur for the process model. To calculate a language for the process model, a scalable approach (but non-deterministic) is to perform a playout of the model to obtain an event log. Let’s first apply the Alpha Miner. Then, we perform the playout of the Petri net using the `STOCHASTIC_PLAYOUT` variant.

```python
if __name__ == "__main__":
    net, im, fm = pm4py.discover_petri_net_alpha(log)
```

We can then calculate the language of the event log:

```python
from pm4py.algo.simulation.playout.petri_net import algorithm as simulator

if __name__ == "__main__":
    playout_log = simulator.apply(
        net, im, fm,
        parameters={simulator.Variants.STOCHASTIC_PLAYOUT.value.Parameters.LOG: log},
        variant=simulator.Variants.STOCHASTIC_PLAYOUT
    )
    model_language = variants_module.get_language(playout_log)
```

Obtaining the language of the model. Then, the Earth Mover Distance is calculated:

- Ensure that both languages contain the same traces: if a language does not contain a trace, it is set to 0.
- Decide on a common ordering (for example, alphabetical) among the keys of the languages.
- Calculate the distance between different keys using a string distance function such as the Levenshtein function.

This results in a number greater than or equal to 0 that expresses the distance between the language of the log and the language of the model. This is an alternative measure for precision. To calculate the Earth Mover Distance, the Python package `pyemd` should be installed (`pip install pyemd`).

The code to apply the Earth Mover Distance is as follows:

```python
from pm4py.algo.evaluation.earth_mover_distance import algorithm as emd_evaluator

if __name__ == "__main__":
    emd = emd_evaluator.apply(model_language, language)
    print(emd)
```

If the running-example log is chosen along with the Alpha Miner model, a value similar to or equal to `0.1733` is obtained.

## WOFLAN

WOFLAN is a popular approach for soundness checking on workflow nets that provides meaningful statistics to the final user. WOFLAN is described in this PhD thesis:
[WOFLAN PhD Thesis](http://www.processmining.org/_media/publications/everbeek_phdthesis.pdf).
The definitions of workflow nets and soundness can also be found at:
[Petri Net Wikipedia](https://en.wikipedia.org/wiki/Petri_net).

WOFLAN is applied to an accepting Petri net (a Petri net with initial and final markings) and follows these steps (the meanings of the steps are detailed in the thesis):

- Checking if the Petri net and the markings are valid.
- Checking if the Petri net is a workflow net.
- Checking if all places are covered by S-components.
- Checking for well-handled pairs.
- Checking for places uncovered in uniform invariants.
- Checking for places uncovered in weighted invariants.
- Checking if the WPD is proper.
- Checking for substates in the MCG.
- Checking for unbounded sequences.
- Checking for dead tasks.
- Checking for live tasks.
- Checking for non-live tasks.
- Checking for sequences leading to deadlocks.

The order of application is described by the picture at the following link: [WOFLAN Steps](static/assets/images/woflan-steps.png). If a step has a positive outcome, "Yes" is written on the corresponding edge. If a step has a negative outcome, "No" is written on the corresponding edge.

Let's see how WOFLAN can be applied. First, we open a XES log.

```python
import pm4py

if __name__ == "__main__":
    log = pm4py.read_xes("tests/input_data/running-example.xes")
```

Then, we discover a model using the Heuristics Miner.

```python
import pm4py

if __name__ == "__main__":
    net, im, fm = pm4py.discover_petri_net_heuristics(log)
```

Next, soundness can be checked by executing:

```python
from pm4py.algo.analysis.woflan import algorithm as woflan

if __name__ == "__main__":
    is_sound = woflan.apply(
        net, im, fm,
        parameters={
            woflan.Parameters.RETURN_ASAP_WHEN_NOT_SOUND: True,
            woflan.Parameters.PRINT_DIAGNOSTICS: False,
            woflan.Parameters.RETURN_DIAGNOSTICS: False
        }
    )
```

In this case, `is_sound` contains a boolean value (`True` if the Petri net is a sound workflow net; `False` otherwise). The list of parameters includes:

Inspect parameters:

| Parameter                          | Description                                                                                                                                               |
|------------------------------------|-----------------------------------------------------------------------------------------------------------------------------------------------------------|
| PRINT_DIAGNOSTICS                  | Enables printing of diagnostics on the Petri net when WOFLAN is executed.                                                                                 |
| RETURN_DIAGNOSTICS                 | Returns a dictionary containing the diagnostics.                                                                                                           |
| RETURN_ASAP_WHEN_NOT_SOUND         | Stops the execution of WOFLAN when a condition determining that the Petri net is not a sound workflow net is found.                                        |

On the provided Petri net, which is not sound, the output of the technique is `False`. To determine why the Petri net is not sound, repeat the execution of the script with `PRINT_DIAGNOSTICS` set to `True` and `RETURN_ASAP_WHEN_NOT_SOUND` set to `False` (to obtain more diagnostics). We get the following messages during execution:

```
Input is ok.
Petri Net is a workflow net.
The following places are not covered by an S-component: [splace_in_decide_check ticket_0, splace_in_check ticket_0, pre_check ticket, splace_in_check ticket_1].
Not well-handled pairs are: [(1, 6), (5, 6), (17, 82), (1, 20), (25, 20), (39, 82), (1, 46), (5, 46), (25, 46), (35, 46), (25, 56), (35, 56), (1, 62), (5, 62), (5, 74), (35, 74), (89, 82)].
The following places are uncovered in uniform invariants: [splace_in_decide_check ticket_0, splace_in_check ticket_0, pre_check ticket, splace_in_check ticket_1]
The following places are uncovered in weighted invariants: [splace_in_decide_check ticket_0, splace_in_check ticket_0, pre_check ticket, splace_in_check ticket_1]
Improper WPD. The following are the improper conditions: [0, 176, 178, 179, 186, 190, 193, 196, 199, 207, 214, 215, 216, 217, 222, 233, 235].
The following sequences are unbounded: [
    [register request, hid_10, hid_3, check ticket, hid_1, examine casually, hid_7, decide, hid_13],
    [register request, hid_9, hid_5, examine thoroughly, hid_8, decide, hid_13],
    [register request, hid_9, hid_5, examine thoroughly, hid_8, decide, hid_14, reinitiate request, hid_16],
    [register request, hid_9, hid_3, hid_5, check ticket, examine thoroughly, hid_8, decide, hid_13],
    [register request, hid_9, hid_3, hid_5, check ticket, examine thoroughly, hid_8, decide, hid_14, reinitiate request, hid_16],
    [register request, hid_9, hid_3, hid_5, check ticket, examine thoroughly, hid_8, decide, hid_14, reinitiate request, hid_17, hid_2, hid_4, examine casually, hid_7, decide, hid_13],
    [register request, hid_9, hid_3, hid_5, check ticket, examine thoroughly, hid_8, decide, hid_14, reinitiate request, hid_17, hid_2, hid_4, examine casually, hid_7, decide, hid_14, reinitiate request, hid_16],
    [register request, hid_9, hid_3, hid_5, check ticket, examine thoroughly, hid_8, decide, hid_14, reinitiate request, hid_17, hid_2, hid_4, examine casually, hid_7, decide, hid_14, reinitiate request, hid_17, hid_2, examine casually, check ticket, hid_7, decide, hid_13],
    [register request, hid_9, hid_3, hid_5, check ticket, examine thoroughly, hid_8, decide, hid_14, reinitiate request, hid_17, hid_2, hid_4, examine casually, hid_7, decide, hid_14, reinitiate request, hid_17, hid_2, examine casually, check ticket, hid_7, decide, hid_14, reinitiate request, hid_16]
]
```

From there, we can see that:

- There are places not covered in an S-component.
- There are no well-handled pairs.
- There are places uncovered in uniform and weighted invariants.
- It is an improper WPD.
- Some sequences are unbounded.

To get the diagnostics in a dictionary, execute the script with:

```python
from pm4py.algo.analysis.woflan import algorithm as woflan

if __name__ == "__main__":
    is_sound, dictio_diagnostics = woflan.apply(
        net, im, fm,
        parameters={
            woflan.Parameters.RETURN_ASAP_WHEN_NOT_SOUND: False,
            woflan.Parameters.PRINT_DIAGNOSTICS: False,
            woflan.Parameters.RETURN_DIAGNOSTICS: True
        }
    )
```

The dictionary `dictio_diagnostics` may contain the following keys (if the computation reaches the corresponding step):

Inspect outputs:

| Key                         | Description |
|-----------------------------|-------------|
| S_C_NET                     |             |
| PLACE_INVARIANTS           |             |
| UNIFORM_PLACE_INVARIANTS   |             |
| S_COMPONENTS                |             |
| UNCOVERED_PLACES_S_COMPONENT|             |
| NOT_WELL_HANDLED_PAIRS      |             |
| LEFT                        |             |
| UNCOVERED_PLACES_UNIFORM    |             |
| WEIGHTED_PLACE_INVARIANTS   |             |
| UNCOVERED_PLACES_WEIGHTED   |             |
| MCG                         |             |
| DEAD_TASKS                  |             |
| R_G_S_C                     |             |
| R_G                         |             |
| LOCKING_SCENARIOS           |             |
| RESTRICTED_COVERABILITY_TREE|             |
