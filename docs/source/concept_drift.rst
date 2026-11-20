Concept drift detection
=======================

Use ``pm4py.algo.concept_drift.algorithm`` to compare process behavior over
time. Choose the variant according to the kind of change you want to
observe. For example, branch probabilities can change while the set of
directly-follows relations stays the same.

.. code-block:: python

   from pm4py.algo.concept_drift import algorithm

   result = algorithm.apply(
       log,
       variant=algorithm.Variants.DFG_FREQUENCY,
       parameters={"window_size": 100, "step": 10, "random_state": 7},
   )
   for alarm in result.changes:
       print(alarm.index, alarm.timestamp, alarm.available_at)
       print(alarm.details["changed_relations"])

Inputs and results
------------------

Trace-based variants accept a pandas DataFrame or legacy EventLog with
complete cases. Event-level monitoring can use partial cases in a
DataFrame or EventStream. DataFrame columns default to ``case:concept:name``,
``concept:name``, and ``time:timestamp``. To override them, pass ``case_id_key``,
``activity_key``, or ``timestamp_key`` in the parameters. DataFrame case
attributes use the ``case:`` prefix. Timestamps are converted to UTC, with
naive timestamps interpreted as UTC. Events with the same timestamp retain
their input order within a trace.

The new variants return a
:class:`~pm4py.algo.concept_drift.result.DriftResult` with the following fields.

* ``observation_unit`` and zero-based ``index`` values identify the analysis
  axis. Trace indices normally follow case completion order. Version
  Clustering, relation invariance, and supervised similarity use first-event
  order. Calendar indices count bins from the first bin in the analysis.
  Event relation indices count events in timestamp order.
* ``scores`` contains evidence at tested boundaries or observations.
  Variants that perform significance tests also report p-values.
* ``changes`` records estimated boundaries and their ``timestamp`` and
  ``available_at``. A sequential detector can estimate a boundary earlier
  than the observation that confirmed it. In retrospective analyses,
  report availability generally coincides with the end of the input.
* ``intervals`` contains inclusive transition bounds when supported.
  ``versions`` records the assigned version at each applicable observation.
* ``metadata`` records the configuration, including the PM4Py version.
  Score and alarm ``details`` can include changed relations, indicator
  values, constraint profiles, model versions, or prediction confidence.

Calling ``algorithm.apply(log)`` still selects the existing Bose-inspired
detector and returns its original tuple of sublogs, Unix timestamps, and
p-values.

Choosing a detector
-------------------

Each variant's ``apply`` docstring describes its parameters.

* **Behavioral relation statistics.** ``BOSE`` monitors eventually-follows
  relation features. ``DFG_FREQUENCY`` is a new combination that compares
  adjacent completed-trace windows using Jensen–Shannon distance and a
  trace-level permutation test or a likelihood-ratio G-test. Both windows
  need edges to estimate their conditional edge frequencies. Set
  ``retrospective=False`` for sequential confirmation.
  ``EVENT_RELATIONS`` adapts the event-stream method of Ostovar et al.
  It compares alpha-plus relation counts with a G-test and can detect a
  change while cases are still running. Pass a DataFrame or EventStream
  for replay, or call ``event_relations.EventStreamDetector.update`` for
  incremental monitoring. Adaptive width is bounded by the observed history.
  The alarm records when the first positive test occurred and when persistence
  confirmed it. The original reference and detection window boundary is
  also recorded.
  `Detecting Drift from Event Streams <https://doi.org/10.1007/978-3-319-46397-1_26>`_.
* **Structural stability.** ``LCDD`` follows the fixed-window form of
  `Local Completeness-based Drift Detection <https://doi.org/10.1109/TSC.2020.3032787>`_.
  The first window is assumed locally complete. Added relations can be
  reported immediately, while disappearance must persist through a detection
  window. The method rebuilds the reference after each alarm.
  ``RELATION_INVARIANCE`` groups nearby boundaries of stable directly-
  and eventually-follows relation histories. It operates retrospectively
  and can expose long-range ordering changes.
  `Relation Invariance <https://doi.org/10.1007/978-3-319-69462-7_33>`_.
  ``GRAPH_METRICS`` compares topology across completed-trace DFG blocks
  with PELT. Connectivity, branching, cycles, and self-loop traffic can
  expose structural shifts. These summaries ignore activity names.
  `Process Drift Detection Using Model-Based Graph Metrics <https://doi.org/10.1145/3040565.3040566>`_.
* **Execution distributions.** ``RUN_DISTRIBUTION`` adapts
  `run-based ProDrift <https://doi.org/10.1109/TKDE.2017.2720601>`_ using
  window-local concurrency and a chi-square test. It supports bounded
  adaptive windows and an optional retrospective mixture check for gradual
  intervals. ``TRACE_VARIANT_FREQUENCY`` compares exact activity
  sequences with Jensen–Shannon distance and whole-trace or block
  permutations. It preserves the observed order of concurrent activities.
  ``EARTH_MOVER`` compares stochastic trace languages with
  normalized edit cost. Set ``time_feature`` to ``"inter_event"`` for gaps
  between event completions or ``"service"`` for elapsed time between an
  event's start and completion. The time-aware adaptation fits per-activity
  timing bins on the supplied log. A retrospective threshold can turn
  excursions in the distance curve into alarms.
  `Time-aware drift detection with EMD <https://doi.org/10.1109/ICPM49681.2020.00016>`_.
* **Calendar indicators.** ``INDICATORS`` applies PELT, Page–Hinkley, or ADWIN.
  Features include absolute arrivals, completions and work in progress, case
  duration, activity frequencies, inter-event gaps, service time, conditional
  resource assignment, handovers, and case composition. Sequential methods
  use raw values with one monitor per feature. Any feature can raise an
  alarm. Calendar replay assumes the first and last observed events identify
  starts and completions in the supplied complete cases. Sequential
  monitoring uses bins closed by the last event timestamp. Set
  ``observation_end`` to use a known later cutoff, including recorded empty
  bins. Retrospective extraction includes the final bin by default.
  ``CV_INDICATORS`` uses the same calendar features and selects a centered
  rolling window separately for each indicator from its coefficient of
  variation curve. It then runs retrospective PELT on each smoothed series.
  The results include the candidate CVs and chosen widths.
  `CVDrift <https://doi.org/10.1007/978-3-032-37877-4_11>`_.
* **Conformance.** ``CONFORMANCE`` is a FAIRY-inspired detector that monitors
  trace alignment fitness with Page–Hinkley or ADWIN. It accepts a Petri net
  or discovers one with Inductive Miner. The reference can stay fixed or be
  relearned from available traces after an alarm. Results record the model
  and training range for each version. Fitness can stay high when valid
  behavior disappears. ``CONFORMANCE_PROFILE`` adds escaping-edge
  precision and segments both metrics jointly with PELT against a fixed
  Petri net. It can detect a path disappearing from the log even if all
  observed traces continue to fit.
  `CRIER <https://doi.org/10.1145/3716169>`_.
* **Declarative profiles.** ``DECLARE_PROFILES`` is a VDD adaptation that
  applies kernel PELT to window statistics for a fixed Declare constraint
  bank. For example, pass ``constraints=[("response", "A", "B")]``. Each
  activated trace counts once. The default confidence divides activated and
  satisfied traces by the window size. Support and violation rate divide
  by activated traces. A window without activations gives confidence
  zero. For support and violation rate, PELT uses zero and the sequential
  modes skip that rule's window. Select ``method="adwin"`` or
  ``method="page_hinkley"`` with explicit constraints to monitor each rule
  as windows close. ADWIN estimates the start of the retained window,
  which can precede the actual transition.
  `Visual Drift Detection <https://arxiv.org/abs/1907.06386>`_.
* **Version discovery.** ``VERSION_CLUSTERING`` uses start-ordered DFG
  windows, cosine similarity, HDBSCAN soft memberships, and penalized RBF
  kernel segmentation. It operates on the full log. Version labels are
  comparable within a run, including when a version recurs.
  `Version Clustering <https://doi.org/10.1007/978-3-032-28110-4_4>`_.
  ``CLUSTER_FREQUENCY`` fits K-means on the first completed traces and
  monitors subsequent changes in cluster shares. The vocabulary and
  cluster IDs stay fixed. Cluster 0 collects unfamiliar profiles and
  optional distance-based outliers.
* **Joint features.** ``MULTIVARIATE`` adapts RBF Maximum Mean Discrepancy
  and energy distance to process observations. It can detect joint changes
  with unchanged marginals. Select ``features=["activity_resource"]`` to
  monitor assignments, or pass a numerical observation matrix to
  ``multivariate.apply_features``. For example, ``indicators.extract_features``
  can produce one row per hour, with the test comparing collections of
  hourly rows. Supply finite values and pass the bin close times as
  ``available_at``. Numeric scaling and automatic kernel bandwidth use the
  two windows under test.
  `Maximum Mean Discrepancy <https://www.jmlr.org/papers/v13/gretton12a.html>`_.
* **Supervised patterns.** ``SUPERVISED_SIMILARITY`` adapts the CV4CDD-4D
  approach. It creates a DFG similarity image and maps the regions returned
  by a trained predictor to trace points or intervals. The lightweight
  classifier can be trained with ``supervised_similarity.fit`` on pairs of
  logs and labeled ``Region`` objects. A caller can also wrap an external
  detector in a callable that returns inclusive window bounds, a drift type,
  and confidence. Published weights are distributed by the authors.
  `CV4CDD-4D <https://doi.org/10.1007/s44311-025-00012-w>`_.

Calibration and dependencies
----------------------------

DFG frequency, trace-variant frequency, cluster frequency, and
multivariate tests use configurable per-window significance, minimum effect, persistence, and alarm separation. By default
permutations exchange whole traces or whole rows. Set
``permutation_block_size`` to exchange contiguous blocks when that is a
better approximation for the observation dependence. A nominal per-window
significance level does not establish a run-wide false-alarm guarantee when
tests are repeated across overlapping windows. In indicator monitoring,
adding features increases the number of opportunities for an alarm. Use
stationary data representative of the process to calibrate alarm settings.

Install ``pm4py[drift]`` to use River ADWIN and HDBSCAN for Version Clustering.
Cluster frequency and the supervised patch classifier use scikit-learn
from ``pm4py[ml]``.
Base PM4Py can construct images and use a supplied predictor.
