API Reference
=============

This page provides an overview of all public ``pm4py`` objects, functions, and methods.

Input (:mod:`pm4py.read`)
-------------------------
``pm4py`` supports importing the following standardized *event data* formats:

  * ``.xes`` files (`xes-standard <https://xes-standard.org/>`_); general interchange format for event data. :meth:`pm4py.read.read_xes`

In case an event log is stored as a ``.csv`` file, ``pandas`` can be used to directly import the event log as a ``data frame`` (`docs <https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html>`_).
``.xes`` files are internally converted to a ``pandas dataframe``, which is the default data structure used by all algorithms implemented in ``pm4py``.

Additional file formats that are currently supported by PM4Py are:

  * ``.bpmn`` files; file format specifying process models in the *BPMN* process modeling formalism :meth:`pm4py.read.read_bpmn`
  * ``.dfg`` files; file format specifying *directly follows graphs* (also referred to as *process maps*) :meth:`pm4py.read.read_dfg`
  * ``.pnml`` files; file format specifying *Petri net* models :meth:`pm4py.read.read_pnml`
  * ``.ptml`` files; file format specifying *Process Tree* models :meth:`pm4py.read.read_ptml`

Importing object-centric event logs is possible given the following formats:

  * automatic format detection from the file extension :meth:`pm4py.read.read_ocel`
  * ``.csv`` specification :meth:`pm4py.read.read_ocel_csv`
  * ``.jsonocel`` specification :meth:`pm4py.read.read_ocel_json`
  * ``.xmlocel`` specification :meth:`pm4py.read.read_ocel_xml`
  * ``.sqlite`` specification :meth:`pm4py.read.read_ocel_sqlite`

Importing object-centric event logs (OCEL2.0) is possible given the following formats:

  * automatic format detection from the file extension :meth:`pm4py.read.read_ocel2`
  * bundled ``.ocel.zip`` CSV/Parquet specification :meth:`pm4py.read.read_ocel2_bundle`
  * compact ``.csv`` specification :meth:`pm4py.read.read_ocel2_csv`
  * ``.xmlocel`` specification :meth:`pm4py.read.read_ocel2_xml`
  * ``.sqlite`` specification :meth:`pm4py.read.read_ocel2_sqlite`
  * ``.jsonocel`` specification :meth:`pm4py.read.read_ocel2_json`


Output (:mod:`pm4py.write`)
----------------------------
Similarly to event data importing, ``pm4py`` supports export functionalities to:

  * ``.bpmn`` files, :meth:`pm4py.write.write_bpmn`
  * ``.dfg`` files, :meth:`pm4py.write.write_dfg`
  * ``.pnml`` files, :meth:`pm4py.write.write_pnml`
  * ``.ptml`` files, :meth:`pm4py.write.write_ptml`
  * ``.xes`` files, :meth:`pm4py.write.write_xes`

Exporting object-centric event logs is possible to the following formats:

  * automatic format detection from the file extension :meth:`pm4py.write.write_ocel`
  * ``.csv`` specification :meth:`pm4py.write.write_ocel_csv`
  * ``.jsonocel`` specification :meth:`pm4py.write.write_ocel_json`
  * ``.xmlocel`` specification :meth:`pm4py.write.write_ocel_xml`
  * ``.sqlite`` specification :meth:`pm4py.write.write_ocel_sqlite`

Exporting object-centric event logs (OCEL2.0) is possible to the following formats:

  * automatic format detection from the file extension :meth:`pm4py.write.write_ocel2`
  * bundled ``.ocel.zip`` CSV/Parquet specification :meth:`pm4py.write.write_ocel2_bundle`
  * compact ``.csv`` specification :meth:`pm4py.write.write_ocel2_csv`
  * ``.xmlocel`` specification :meth:`pm4py.write.write_ocel2_xml`
  * ``.sqlite`` specification :meth:`pm4py.write.write_ocel2_sqlite`
  * ``.jsonocel`` specification :meth:`pm4py.write.write_ocel2_json`


Conversion (:mod:`pm4py.convert`)
---------------------------------
Several conversions are available from/to different objects supported by ``pm4py``.
The following conversions are currently available:

  * :meth:`pm4py.convert.convert_to_bpmn` converts a process model to BPMN
  * :meth:`pm4py.convert.convert_to_petri_net` converts a process model to a Petri net
  * :meth:`pm4py.convert.convert_to_process_tree` converts a process model to a process tree
  * :meth:`pm4py.convert.convert_to_powl` converts a process model to a POWL model
  * :meth:`pm4py.convert.convert_to_reachability_graph` converts a process model to a reachability graph
  * :meth:`pm4py.convert.convert_log_to_ocel` converts an event log to an object-centric event log
  * :meth:`pm4py.convert.convert_log_to_networkx` converts a traditional event log (dataframe) to a directed graph (NetworkX)
  * :meth:`pm4py.convert.convert_log_to_time_intervals` converts an event log to time intervals between consecutive events.
  * :meth:`pm4py.convert.convert_ocel_to_networkx` converts an object-centric event log to a directed graph (NetworkX)
  * :meth:`pm4py.convert.convert_petri_net_to_networkx` converts an accepting Petri net to a directed graph (NetworkX)
  * :meth:`pm4py.convert.convert_petri_net_type` changes the Petri net internal type


Process Discovery (:mod:`pm4py.discovery`)
------------------------------------------
Process discovery algorithms discover a process model that describes the process execution, as stored in the event log.
``PM4Py`` implements a variety of different process discovery algorithms.
These different algorithms return different kinds of models, i.e., models with *imprecise execution semantics*, *procedural process models*, and *declarative process models*.
Among the models with *imprecise execution semantics*, ``pm4py`` currently supports:

  * :meth:`pm4py.discovery.discover_dfg`; discovers a *directly follows graph* annotated with frequency information (based on the log).
  * :meth:`pm4py.discovery.discover_directly_follows_graph`; alias for discovering a frequency *directly follows graph*.
  * :meth:`pm4py.discovery.discover_dfg_typed`; discovers a typed *directly follows graph* object.
  * :meth:`pm4py.discovery.discover_performance_dfg`; discovers a *directly follows graph* annotated with performance information (based on the log).
  * :meth:`pm4py.discovery.correlation_miner`; discovers a frequency or performance *directly follows graph* from an event log without a case identifier.

Among *procedural process models*, ``pm4py`` currently supports:

  * :meth:`pm4py.discovery.discover_petri_net_alpha`; discovers a *Petri net* using the Alpha Miner algorithm.
  * :meth:`pm4py.discovery.discover_petri_net_alpha_plus`; discovers a *Petri net* using the deprecated Alpha+ Miner algorithm.
  * :meth:`pm4py.discovery.discover_petri_net_inductive`; discovers a *Petri net* using the Inductive Miner algorithm.
  * :meth:`pm4py.discovery.discover_petri_net_heuristics`; discovers a *Petri net* using the Heuristics Miner algorithm.
  * :meth:`pm4py.discovery.discover_petri_net_ilp`; discovers a *Petri net* using the ILP Miner algorithm.
  * :meth:`pm4py.discovery.discover_petri_net_genetic`; discovers a *Petri net* using the Genetic Miner algorithm.
  * :meth:`pm4py.discovery.discover_process_tree_inductive`; discovers a *process tree* using the Inductive Miner algorithm.
  * :meth:`pm4py.discovery.discover_bpmn_inductive`; discovers a *BPMN model* using the Inductive Miner algorithm.
  * :meth:`pm4py.discovery.discover_bpmn_split_miner`; discovers a *BPMN model* using the Split Miner algorithm.
  * :meth:`pm4py.discovery.discover_heuristics_net`; discovers a *heuristics net* using the Heuristics Miner algorithm.
  * :meth:`pm4py.discovery.discover_footprints`; discovers the *footprints matrix* of the log or the model.
  * :meth:`pm4py.discovery.discover_powl`; discovers a *partial order workflow language* (POWL) model.
  * :meth:`pm4py.discovery.discover_otg`; discovers an *object-type graph* from an object-centric event log.
  * :meth:`pm4py.discovery.discover_etot`; discovers an *event type-object type graph* from an object-centric event log.

Among *declarative process models*, ``pm4py`` currently supports:

  * :meth:`pm4py.discovery.discover_declare`; discovers a *DECLARE* model.
  * :meth:`pm4py.discovery.discover_log_skeleton`; discovers a *log skeleton*.
  * :meth:`pm4py.discovery.discover_temporal_profile`; discovers a *temporal profile*.


Concept Drift (:mod:`pm4py.algo.concept_drift`)
---------------------------------------------
:func:`pm4py.algo.concept_drift.algorithm.apply` dispatches concept-drift
detectors. See :doc:`concept_drift` for variant options, time conventions,
and result fields.

Conformance Checking (:mod:`pm4py.conformance`)
-----------------------------------------------
Conformance checking techniques compare a process model with an event log of the same process. The goal is to check if the event log conforms to the model, and vice versa.
Among procedural process models, ``pm4py`` currently supports:

  * :meth:`pm4py.conformance.conformance_diagnostics_token_based_replay`; token-based replay between the event log and a *Petri net*.
  * :meth:`pm4py.conformance.conformance_diagnostics_alignments`; alignment-based replay between the event log and a *Petri net*.
  * :meth:`pm4py.conformance.conformance_diagnostics_footprints`; footprints-based conformance diagnostics.
  * :meth:`pm4py.conformance.fitness_token_based_replay`; evaluation of the fitness between an event log and a *Petri net* using token-based replay.
  * :meth:`pm4py.conformance.fitness_alignments`; evaluation of the fitness between an event log and a *Petri net* using alignments.
  * :meth:`pm4py.conformance.fitness_footprints`; evaluation of the fitness based on footprints.
  * :meth:`pm4py.conformance.precision_token_based_replay`; evaluation of the precision between an event log and a *Petri net* using token-based replay.
  * :meth:`pm4py.conformance.precision_alignments`; evaluation of the precision between an event log and a *Petri net* using alignments.
  * :meth:`pm4py.conformance.precision_footprints`; evaluation of the precision based on footprints.
  * :meth:`pm4py.conformance.generalization_tbr`; evaluation of the generalization between an event log and a *Petri net* using token-based replay.
  * :meth:`pm4py.conformance.replay_prefix_tbr`; replays a prefix (list of activities) on a given *Petri net*, using Token-Based Replay.
  * :meth:`pm4py.conformance.check_is_fitting`; checks whether a trace fits a process model.

Among declarative process models, ``pm4py`` currently supports:

  * :meth:`pm4py.conformance.conformance_log_skeleton`; conformance checking using the *log skeleton*.
  * :meth:`pm4py.conformance.conformance_declare`; conformance checking using a *DECLARE model*.
  * :meth:`pm4py.conformance.conformance_temporal_profile`; conformance checking using the *temporal profile*.

Among object-centric process models, ``pm4py`` currently supports:

  * :meth:`pm4py.conformance.conformance_ocdfg`; conformance checking using an *object-centric directly-follows graph*.
  * :meth:`pm4py.conformance.conformance_otg`; conformance checking using an *object-type graph*.
  * :meth:`pm4py.conformance.conformance_etot`; conformance checking using an *event type-object type graph*.


Visualization (:mod:`pm4py.vis`)
---------------------------------
The ``pm4py`` library implements basic visualizations of process models and statistics.
Among the on-screen visualizations, ``pm4py`` currently supports:

  * :meth:`pm4py.vis.view_petri_net`; views a *Petri net* model.
  * :meth:`pm4py.vis.view_dfg`; views a *directly-follows graph* annotated with the frequency.
  * :meth:`pm4py.vis.view_performance_dfg`; views a *directly-follows graph* annotated with the performance.
  * :meth:`pm4py.vis.view_process_tree`; views a *process tree*.
  * :meth:`pm4py.vis.view_bpmn`; views a *BPMN model*.
  * :meth:`pm4py.vis.view_heuristics_net`; views a *heuristics net*.
  * :meth:`pm4py.vis.view_dotted_chart`; views a *dotted chart*.
  * :meth:`pm4py.vis.view_sna`; views the results of a *social network analysis*.
  * :meth:`pm4py.vis.view_case_duration_graph`; views the *case duration graph*.
  * :meth:`pm4py.vis.view_events_per_time_graph`; views the *events per time graph*.
  * :meth:`pm4py.vis.view_performance_spectrum`; views the *performance spectrum*.
  * :meth:`pm4py.vis.view_events_distribution_graph`; views the *events distribution graph*.
  * :meth:`pm4py.vis.view_ocdfg`; views an *object-centric directly-follows graph*.
  * :meth:`pm4py.vis.view_ocpn`; views an *object-centric Petri net*.
  * :meth:`pm4py.vis.view_object_graph`; views an *object-based graph*.
  * :meth:`pm4py.vis.view_network_analysis`; views the results of a *network analysis*.
  * :meth:`pm4py.vis.view_transition_system`; views the results of a *transition system*.
  * :meth:`pm4py.vis.view_prefix_tree`; views a *prefix tree*.
  * :meth:`pm4py.vis.view_alignments`; views the *alignments table*.
  * :meth:`pm4py.vis.view_footprints`; views a *footprints table*.
  * :meth:`pm4py.vis.view_powl`; views a *POWL model*.

We also offer some methods to store the visualizations on the disk:

  * :meth:`pm4py.vis.save_vis_petri_net`; saves the visualization of a *Petri net* model.
  * :meth:`pm4py.vis.save_vis_dfg`; saves the visualization of a *directly-follows graph* annotated with the frequency.
  * :meth:`pm4py.vis.save_vis_performance_dfg`; saves the visualization of a *directly-follows graph* annotated with the performance.
  * :meth:`pm4py.vis.save_vis_process_tree`; saves the visualization of a *process tree*.
  * :meth:`pm4py.vis.save_vis_bpmn`; saves the visualization of a *BPMN model*.
  * :meth:`pm4py.vis.save_vis_heuristics_net`; saves the visualization of a *heuristics net*.
  * :meth:`pm4py.vis.save_vis_dotted_chart`; saves the visualization of a *dotted chart*.
  * :meth:`pm4py.vis.save_vis_sna`; saves the visualization of the results of a *social network analysis*.
  * :meth:`pm4py.vis.save_vis_case_duration_graph`; saves the visualization of the *case duration graph*.
  * :meth:`pm4py.vis.save_vis_events_per_time_graph`; saves the visualization of the *events per time graph*.
  * :meth:`pm4py.vis.save_vis_performance_spectrum`; saves the visualization of the *performance spectrum*.
  * :meth:`pm4py.vis.save_vis_events_distribution_graph`; saves the visualization of the *events distribution graph*.
  * :meth:`pm4py.vis.save_vis_ocdfg`; saves the visualization of an *object-centric directly-follows graph*.
  * :meth:`pm4py.vis.save_vis_ocpn`; saves the visualization of an *object-centric Petri net*.
  * :meth:`pm4py.vis.save_vis_object_graph`; saves the visualization of an *object-based graph*.
  * :meth:`pm4py.vis.save_vis_network_analysis`; saves the visualization of the results of a *network analysis*.
  * :meth:`pm4py.vis.save_vis_transition_system`; saves the visualization of the results of a *transition system*.
  * :meth:`pm4py.vis.save_vis_prefix_tree`; saves the visualization of a *prefix tree*.
  * :meth:`pm4py.vis.save_vis_alignments`; saves the visualization of the *alignments table*.
  * :meth:`pm4py.vis.save_vis_footprints`; saves the visualization of the *footprints table*.
  * :meth:`pm4py.vis.save_vis_powl`; saves the visualization of a *POWL model*.


Statistics (:mod:`pm4py.stats`)
-------------------------------
Different statistics that can be computed on top of event logs are proposed, including:

  * :meth:`pm4py.stats.get_start_activities`; gets the *start activities* from the event log.
  * :meth:`pm4py.stats.get_end_activities`; gets the *end activities* from the event log.
  * :meth:`pm4py.stats.get_event_attributes`; gets the *attributes at the event level* of the event log.
  * :meth:`pm4py.stats.get_trace_attributes`; gets the *attributes at the trace level* of the event log.
  * :meth:`pm4py.stats.get_event_attribute_values`; gets the values of an *attribute at the event level* of the event log.
  * :meth:`pm4py.stats.get_trace_attribute_values`; gets the values of an *attribute at the trace level* of the event log.
  * :meth:`pm4py.stats.get_variants`; gets the *variants* of the event log.
  * :meth:`pm4py.stats.get_variants_as_tuples`; gets the *variants* of the event log as tuples.
  * :meth:`pm4py.stats.split_by_process_variant`; splits an event log into sub-dataframes for each process variant.
  * :meth:`pm4py.stats.get_variants_paths_duration`; method that associates to a log object a Pandas dataframe aggregated by variants and positions (inside the variant).
  * :meth:`pm4py.stats.get_minimum_self_distances`; gets the *minimum self-distances* from the event log.
  * :meth:`pm4py.stats.get_minimum_self_distance_witnesses`; gets the witnesses of *minimum self-distances* from the event log.
  * :meth:`pm4py.stats.get_frequent_trace_segments`; gets the *traces* (segments of activities) of the event log.
  * :meth:`pm4py.stats.get_case_arrival_average`; gets the *average case arrival rate* from the event log.
  * :meth:`pm4py.stats.get_rework_cases_per_activity`; gets the number of cases with rework per activity.
  * :meth:`pm4py.stats.get_case_overlap`; gets the number of concurrently open cases for each case.
  * :meth:`pm4py.stats.get_cycle_time`; gets the *cycle time* from the event log.
  * :meth:`pm4py.stats.get_all_case_durations`; gets the list of *case durations* for the cases of the event log.
  * :meth:`pm4py.stats.get_case_duration`; gets the *case duration* of a specific case in the log.
  * :meth:`pm4py.stats.get_activity_position_summary`; gets the position summary of activities in the traces.
  * :meth:`pm4py.stats.get_process_cube`; builds a two-dimensional process cube from a feature table.
  * :meth:`pm4py.stats.get_stochastic_language`; gets the *stochastic language* of an event log or a process model.
  * :meth:`pm4py.stats.get_service_time`; gets the average *service time* per activity.


Filtering (:mod:`pm4py.filtering`)
-----------------------------------
Filtering is the restriction of the event log to a subset of the behavior.
Different methods are offered in PM4Py for traditional event logs (.xes, .csv), including:

  * :meth:`pm4py.filtering.filter_start_activities`; filters the *start activities* of the event log.
  * :meth:`pm4py.filtering.filter_end_activities`; filters the *end activities* of the event log.
  * :meth:`pm4py.filtering.filter_event_attribute_values`; filters the values of an *attribute at the event level* of the event log.
  * :meth:`pm4py.filtering.filter_trace_attribute_values`; filters the values of an *attribute at the trace level* of the event log.
  * :meth:`pm4py.filtering.filter_variants`; filters the *variants* of an event log.
  * :meth:`pm4py.filtering.filter_directly_follows_relation`; filters the *DF-relations* of an event log.
  * :meth:`pm4py.filtering.filter_eventually_follows_relation`; filters the *EF-relations* of an event log.
  * :meth:`pm4py.filtering.filter_time_range`; filters an event log on a temporal interval.
  * :meth:`pm4py.filtering.filter_between`; filters an event log between a given couple of activities.
  * :meth:`pm4py.filtering.filter_case_size`; filters an event log based on the size of the cases.
  * :meth:`pm4py.filtering.filter_case_performance`; filters an event log based on the throughput time of the cases.
  * :meth:`pm4py.filtering.filter_activities_rework`; filters an event log by looking at the cases where a given activity is executed a different number of times.
  * :meth:`pm4py.filtering.filter_paths_performance`; filters an event log by examining the performance of the paths between two activities.
  * :meth:`pm4py.filtering.filter_variants_top_k`; filters an event log keeping the top-K variants.
  * :meth:`pm4py.filtering.filter_variants_by_coverage_percentage`; filters an event log keeping the variants covering the specified percentage of cases.
  * :meth:`pm4py.filtering.filter_prefixes`; filters the prefixes of an activity.
  * :meth:`pm4py.filtering.filter_suffixes`; filters the suffixes of an activity.
  * :meth:`pm4py.filtering.filter_trace_segments`; filters based on the given traces (segments of activities).
  * :meth:`pm4py.filtering.filter_four_eyes_principle`; applies the *Four-Eyes principle* on the event log (LTL).
  * :meth:`pm4py.filtering.filter_activity_done_different_resources`; filters the cases where an activity is repeated by different resources (LTL).
  * :meth:`pm4py.filtering.filter_log_relative_occurrence_event_attribute`; filters event attribute values based on relative occurrence.

Filtering techniques are also available on directly-follows graphs:

  * :meth:`pm4py.filtering.filter_dfg_activities_percentage`; filters a DFG by keeping a percentage of activities.
  * :meth:`pm4py.filtering.filter_dfg_paths_percentage`; filters a DFG by keeping a percentage of paths.

Also, some filtering techniques are offered on top of object-centric event logs:

  * :meth:`pm4py.filtering.filter_ocel_event_attribute`; filters the events of an object-centric event log having a given value for an attribute.
  * :meth:`pm4py.filtering.filter_ocel_object_attribute`; filters the objects of an object-centric event log having a given value for an attribute.
  * :meth:`pm4py.filtering.filter_ocel_object_types_allowed_activities`; filters the relations between events (activities) and objects (object types) in an object-centric event log.
  * :meth:`pm4py.filtering.filter_ocel_object_per_type_count`; filters the objects of an object-centric event log having at least the specified number of objects per object type.
  * :meth:`pm4py.filtering.filter_ocel_start_events_per_object_type`; filters the events of an object-centric event log that start the lifecycle of an object of a given object type.
  * :meth:`pm4py.filtering.filter_ocel_end_events_per_object_type`; filters the events of an object-centric event log that end the lifecycle of an object of a given object type.
  * :meth:`pm4py.filtering.filter_ocel_events_timestamp`; filters the events of an object-centric event log based on a timestamp range.
  * :meth:`pm4py.filtering.filter_ocel_object_types`; filters a specified collection of object types from the object-centric event log.
  * :meth:`pm4py.filtering.filter_ocel_events`; filters a specified collection of event identifiers from the object-centric event log.
  * :meth:`pm4py.filtering.filter_ocel_objects`; filters a specified collection of object identifiers from the object-centric event log.
  * :meth:`pm4py.filtering.filter_ocel_activities_connected_object_type`; filters an object-centric event log on the activities connected to a given object type.
  * :meth:`pm4py.filtering.filter_ocel_cc_object`; filters a connected component from the object-centric event log to which the object with the provided identifier belongs.
  * :meth:`pm4py.filtering.filter_ocel_cc_length`; filters the connected components from an object-centric event log having a number of objects falling within a provided range.
  * :meth:`pm4py.filtering.filter_ocel_cc_otype`; filters the connected components from an object-centric event log having at least one object of the specified object type.
  * :meth:`pm4py.filtering.filter_ocel_cc_activity`; filters the connected components from an object-centric event log having at least one event with the specified activity.


Machine Learning (:mod:`pm4py.ml`)
-----------------------------------
PM4Py offers some features useful for the application of machine learning techniques.
Among those:

  * :meth:`pm4py.ml.split_train_test`; splits an event log into a *training event log* (default 80% of the cases) and a *test event log* (default 20% of the cases).
  * :meth:`pm4py.ml.get_prefixes_from_log`; gets fixed-length prefixes for the cases of an event log.
  * :meth:`pm4py.ml.extract_features_dataframe`; extracts machine learning features from an event log.
  * :meth:`pm4py.ml.extract_ocel_features`; extracts machine learning features from an object-centric event log.
  * :meth:`pm4py.ml.extract_temporal_features_dataframe`; extracts temporal features from an event log.
  * :meth:`pm4py.ml.extract_target_vector`; extracts from a log object the target vector for a specific ML use case.
  * :meth:`pm4py.ml.extract_outcome_enriched_dataframe`; inserts additional columns in the dataframe which are computed on the overall case, so they model the outcome of the case.


Simulation (:mod:`pm4py.sim`)
-----------------------------------
We offer different simulation algorithms that, starting from a model, are able to produce an output that follows the model and the different rules provided by the user.
Among those:

  * :meth:`pm4py.sim.play_out`; performs the play-out of a process model to obtain an event log.
  * :meth:`pm4py.sim.generate_process_tree`; generates a process tree with the desired number of nodes.


Object-Centric Process Mining (:mod:`pm4py.ocel`)
--------------------------------------------------
Traditional event logs, used by mainstream process mining techniques, require the events to be related to a case. A case is a set of events for a particular purpose. A case notion is a criterion to assign a case to the events.

However, in real processes, this leads to two problems:

* If we consider the Order-to-Cash process, an order could be related to many different deliveries. If we consider the delivery as the case notion, the same event of Create Order needs to be replicated in different cases (all the deliveries involving the order). This is called the convergence problem.
* If we consider the Order-to-Cash process, an order could contain different order items, each with a different lifecycle. If we consider the order as the case notion, several instances of the activities for the single items may be contained in the case, and this makes the frequency/performance annotation of the process problematic. This is called the divergence problem.

Object-centric event logs relax the assumption that an event is related to exactly one case. Indeed, an event can be related to different objects of different object types.

Essentially, we can describe the different components of an object-centric event log as:

* Events, having an identifier, an activity, a timestamp, a list of related objects, and a dictionary of other attributes.
* Objects, having an identifier, a type, and a dictionary of other attributes.
* Attribute names, e.g., the possible keys for the attributes of the event/object attribute map.
* Object types, e.g., the possible types for the objects.

In PM4Py, we offer object-centric process mining features:

  * :meth:`pm4py.ocel.ocel_get_object_types`; gets the object types from an object-centric event log.
  * :meth:`pm4py.ocel.ocel_get_attribute_names`; gets the attribute names from an object-centric event log.
  * :meth:`pm4py.ocel.ocel_flattening`; flattens an object-centric event log with the selection of an object type.
  * :meth:`pm4py.ocel.ocel_object_type_activities`; gets the activities related to an object type in an object-centric event log.
  * :meth:`pm4py.ocel.ocel_objects_ot_count`; counts the objects for an object type.
  * :meth:`pm4py.ocel.ocel_temporal_summary`; returns the temporal summary from an object-centric event log.
  * :meth:`pm4py.ocel.ocel_objects_summary`; returns the objects summary from an object-centric event log.
  * :meth:`pm4py.ocel.ocel_objects_interactions_summary`; returns the objects interactions from an object-centric event log.
  * :meth:`pm4py.ocel.sample_ocel_objects`; returns a sampled object-centric event log by picking a subset of the objects from the original one.
  * :meth:`pm4py.ocel.sample_ocel_connected_components`; returns a sampled object-centric event log containing the provided number of connected components.
  * :meth:`pm4py.ocel.ocel_drop_duplicates`; drops relations between events and objects happening at the same time.
  * :meth:`pm4py.ocel.ocel_merge_duplicates`; merges events in the OCEL that are happening with the same activity at the same timestamp.
  * :meth:`pm4py.ocel.ocel_sort_by_additional_column`; sorts OCEL events by timestamp and an additional column.
  * :meth:`pm4py.ocel.ocel_add_index_based_timedelta`; adds small index-based timedeltas to preserve event ordering.
  * :meth:`pm4py.ocel.ocel_o2o_enrichment`; enriches the O2O table of the OCEL with the graph-based relationships.
  * :meth:`pm4py.ocel.ocel_e2o_lifecycle_enrichment`; enriches the relations table of the OCEL with lifecycle-based information.
  * :meth:`pm4py.ocel.cluster_equivalent_ocel`; performs a clustering of the objects of an OCEL based on lifecycle/interactions similarity.
  * :meth:`pm4py.ocel.ocel_drill_down`; applies an OCEL drill-down operation on an object type using an object attribute.
  * :meth:`pm4py.ocel.ocel_roll_up`; applies an OCEL roll-up operation on tuple-style object sub-types.
  * :meth:`pm4py.ocel.ocel_unfold`; unfolds an event type by a related object type.
  * :meth:`pm4py.ocel.ocel_fold`; folds an unfolded event type back to its original event type.

Some object-centric process discovery algorithms are also offered:

  * :meth:`pm4py.ocel.discover_ocdfg`; discovers an object-centric directly-follows graph from the object-centric event log.
  * :meth:`pm4py.ocel.discover_oc_petri_net`; discovers an object-centric Petri net from the object-centric event log.
  * :meth:`pm4py.ocel.discover_objects_graph`; discovers an object-based graph from the object-centric event log.


LLM Integration (:mod:`pm4py.llm`)
-----------------------------------
The following methods provide just the abstractions of the given objects:

  * :meth:`pm4py.llm.abstract_dfg`; provides the DFG abstraction of a traditional event log
  * :meth:`pm4py.llm.abstract_variants`; provides the variants abstraction of a traditional event log
  * :meth:`pm4py.llm.abstract_log_attributes`; provides the abstraction of the attributes/columns of the event log
  * :meth:`pm4py.llm.abstract_log_features`; provides the abstraction of the machine learning features obtained from an event log
  * :meth:`pm4py.llm.abstract_case`; provides the abstraction of a case (collection of events)
  * :meth:`pm4py.llm.abstract_ocel`; provides the abstraction of an object-centric event log (list of events and objects)
  * :meth:`pm4py.llm.abstract_ocel_ocdfg`; provides the abstraction of an object-centric event log (OC-DFG)
  * :meth:`pm4py.llm.abstract_ocel_features`; provides the abstraction of an object-centric event log (features for ML)
  * :meth:`pm4py.llm.abstract_event_stream`; provides an abstraction of the (last) events of the stream related to a traditional event log
  * :meth:`pm4py.llm.abstract_temporal_profile`; provides the abstraction of a temporal profile model
  * :meth:`pm4py.llm.abstract_petri_net`; provides the abstraction of a Petri net
  * :meth:`pm4py.llm.abstract_declare`; provides the abstraction of a DECLARE model
  * :meth:`pm4py.llm.abstract_log_skeleton`; provides the abstraction of a log skeleton model
  * :meth:`pm4py.llm.explain_visualization`; explains one of the visualizations provided in PM4Py using LVMs.

The following methods can be executed directly against the LLM APIs:

  * :meth:`pm4py.llm.openai_query`; executes a prompt against OpenAI, returning the response as a string
  * :meth:`pm4py.llm.google_query`; executes a prompt against Google APIs, returning the response as a string
  * :meth:`pm4py.llm.anthropic_query`; executes a prompt against Anthropic APIs, returning the response as a string

Additional LLM-based helpers are available:

  * :meth:`pm4py.llm.clustering`; clusters variants of an event log using an LLM.
  * :meth:`pm4py.llm.nlp_to_log_query`; translates natural language into a SQL query on an event log.
  * :meth:`pm4py.llm.nlp_to_log_filter`; translates natural language into a SQL-based event log filter.
  * :meth:`pm4py.llm.automated_hypotheses_formulation`; formulates hypotheses on event data using an LLM.


Basic Connectors (:mod:`pm4py.connectors`)
-------------------------------------------
We offer some basic connectors to get an event log for some processes:

  * :meth:`pm4py.connectors.extract_log_outlook_mails`; extracts a traditional Pandas dataframe representing Outlook mails
  * :meth:`pm4py.connectors.extract_log_outlook_calendar`; extracts a traditional Pandas dataframe representing the Outlook calendar
  * :meth:`pm4py.connectors.extract_log_windows_events`; extracts a traditional Pandas dataframe containing the Windows events registry
  * :meth:`pm4py.connectors.extract_log_chrome_history`; extracts a traditional Pandas dataframe containing the Chrome navigation history
  * :meth:`pm4py.connectors.extract_log_firefox_history`; extracts a traditional Pandas dataframe containing the Firefox navigation history
  * :meth:`pm4py.connectors.extract_log_github`; extracts a traditional Pandas dataframe of a GitHub repository (issues management)
  * :meth:`pm4py.connectors.extract_log_camunda_workflow`; extracts a traditional Pandas dataframe from the database supporting Camunda
  * :meth:`pm4py.connectors.extract_log_sap_o2c`; extracts a traditional Pandas dataframe from the database supporting SAP (O2C process)
  * :meth:`pm4py.connectors.extract_log_sap_accounting`; extracts a traditional Pandas dataframe from the database supporting SAP (Accounting process)
  * :meth:`pm4py.connectors.extract_ocel_outlook_mails`; extracts an object-centric event log representing Outlook mails
  * :meth:`pm4py.connectors.extract_ocel_outlook_calendar`; extracts an object-centric event log representing the Outlook calendar
  * :meth:`pm4py.connectors.extract_ocel_windows_events`; extracts an object-centric event log representing the Windows events
  * :meth:`pm4py.connectors.extract_ocel_chrome_history`; extracts an object-centric event log representing the Chrome history
  * :meth:`pm4py.connectors.extract_ocel_firefox_history`; extracts an object-centric event log representing the Firefox history
  * :meth:`pm4py.connectors.extract_ocel_github`; extracts an object-centric event log of a GitHub repository (issues management)
  * :meth:`pm4py.connectors.extract_ocel_camunda_workflow`; extracts an object-centric event log from the database supporting Camunda
  * :meth:`pm4py.connectors.extract_ocel_sap_o2c`; extracts an object-centric event log from the database supporting SAP (O2C process)
  * :meth:`pm4py.connectors.extract_ocel_sap_accounting`; extracts an object-centric event log from the database supporting SAP (Accounting process)


Social Network Analysis (:mod:`pm4py.org`)
-------------------------------------------
We offer different algorithms for the analysis of the organizational networks starting from an event log:

  * :meth:`pm4py.org.discover_handover_of_work_network`; calculates the Handover of Work metric from the event log.
  * :meth:`pm4py.org.discover_working_together_network`; calculates the Working Together metric from the event log.
  * :meth:`pm4py.org.discover_activity_based_resource_similarity`; calculates the activity-based resource similarity.
  * :meth:`pm4py.org.discover_subcontracting_network`; calculates the Subcontracting metric from the event log.
  * :meth:`pm4py.org.discover_organizational_roles`; discovers the organizational roles from the event log.
  * :meth:`pm4py.org.discover_network_analysis`; discovers the network analysis from the event log.


Privacy (:mod:`pm4py.privacy`)
------------------------------------------
We offer the following algorithms for the anonymization of event logs:

  * :meth:`pm4py.privacy.anonymize_differential_privacy`; PRIPEL (Privacy-preserving event log publishing with contextual information) is a framework to publish event logs that fulfill differential privacy.


Utilities (:mod:`pm4py.utils`)
-------------------------------
Other algorithms, which do not belong to the aforementioned categories, are collected in this section:

  * :meth:`pm4py.utils.format_dataframe`; ensures the correct formatting of the Pandas dataframe.
  * :meth:`pm4py.utils.parse_process_tree`; parses a process tree from a string.
  * :meth:`pm4py.utils.parse_powl_model_string`; parses a POWL model from a string.
  * :meth:`pm4py.utils.parse_event_log_string`; parses an event log from a collection of comma-separated traces.
  * :meth:`pm4py.utils.project_on_event_attribute`; projects an event log on top of a given attribute (e.g., the activity), obtaining a list of lists of values for the attribute.
  * :meth:`pm4py.utils.sample_cases`; samples a traditional event log, returning the specified number of cases.
  * :meth:`pm4py.utils.sample_events`; samples a traditional event log / OCEL, returning the specified number of events.
  * :meth:`pm4py.utils.serialize`; serializes mainstream PM4Py objects as strings.
  * :meth:`pm4py.utils.deserialize`; deserializes mainstream PM4Py objects given their string representation.
  * :meth:`pm4py.utils.is_polars_lazyframe`; checks whether the provided dataframe is a Polars LazyFrame.
  * :meth:`pm4py.utils.get_properties`; collects common PM4Py parameter keys for a log object.
  * :meth:`pm4py.utils.set_classifier`; sets the specified classifier on an event log.
  * :meth:`pm4py.analysis.cluster_log`; clusters a log into sublogs using the provided clusterer.
  * :meth:`pm4py.analysis.insert_case_service_waiting_time`; inserts, for each case, the service and waiting time.
  * :meth:`pm4py.analysis.insert_case_arrival_finish_rate`; inserts the case arrival/finish rate.
  * :meth:`pm4py.analysis.insert_artificial_start_end`; inserts artificial start/end activities in the event log.
  * :meth:`pm4py.analysis.compute_emd`; computes the Earth-Mover Distance between two languages.
  * :meth:`pm4py.analysis.check_is_workflow_net`; checks if a Petri net is a workflow net.
  * :meth:`pm4py.analysis.check_is_sound`; checks if a Petri net is a sound workflow net.
  * :meth:`pm4py.analysis.check_soundness`; checks if a Petri net is a sound workflow net (using Woflan).
  * :meth:`pm4py.analysis.solve_marking_equation`; solves the marking equation.
  * :meth:`pm4py.analysis.solve_extended_marking_equation`; solves the extended marking equation.
  * :meth:`pm4py.analysis.construct_synchronous_product_net`; constructs the synchronous product net between a trace and a Petri net.
  * :meth:`pm4py.analysis.maximal_decomposition`; performs the maximal decomposition of the given Petri net.
  * :meth:`pm4py.analysis.generate_marking`; generates a Marking object from a textual representation.
  * :meth:`pm4py.analysis.reduce_petri_net_invisibles`; reduces the invisible transitions of a Petri net when possible.
  * :meth:`pm4py.analysis.reduce_petri_net_implicit_places`; reduces the implicit places in the Petri net (using MURATA).
  * :meth:`pm4py.analysis.get_enabled_transitions`; gets the transitions enabled in a given marking.
  * :meth:`pm4py.analysis.simplicity_petri_net`; computes the simplicity metric on the given Petri net.
  * :meth:`pm4py.analysis.behavioral_similarity`; computes the behavioral similarity between two process models.
  * :meth:`pm4py.analysis.structural_similarity`; computes the structural similarity between two process models.
  * :meth:`pm4py.analysis.embeddings_similarity`; computes the embeddings similarity between two process models.
  * :meth:`pm4py.analysis.label_sets_similarity`; computes the label-sets-similarity between two process models.
  * :meth:`pm4py.analysis.get_activity_labels`; gets the activity labels from the given event log or process model.
  * :meth:`pm4py.analysis.replace_activity_labels`; uses a substitution dictionary to replace the names of the activities in the process model.
  * :meth:`pm4py.analysis.map_labels_from_second_model`; maps the activity labels of the second process model on top of the first.


List of Methods
------------------------------------------

.. autosummary::

   pm4py.read
   pm4py.read.read_bpmn
   pm4py.read.read_dfg
   pm4py.read.read_pnml
   pm4py.read.read_ptml
   pm4py.read.read_xes
   pm4py.read.read_ocel
   pm4py.read.read_ocel_csv
   pm4py.read.read_ocel_json
   pm4py.read.read_ocel_xml
   pm4py.read.read_ocel_sqlite
   pm4py.read.read_ocel2
   pm4py.read.read_ocel2_bundle
   pm4py.read.read_ocel2_csv
   pm4py.read.read_ocel2_xml
   pm4py.read.read_ocel2_sqlite
   pm4py.read.read_ocel2_json
   pm4py.write
   pm4py.write.write_bpmn
   pm4py.write.write_dfg
   pm4py.write.write_pnml
   pm4py.write.write_ptml
   pm4py.write.write_xes
   pm4py.write.write_ocel
   pm4py.write.write_ocel_csv
   pm4py.write.write_ocel_json
   pm4py.write.write_ocel_xml
   pm4py.write.write_ocel_sqlite
   pm4py.write.write_ocel2
   pm4py.write.write_ocel2_bundle
   pm4py.write.write_ocel2_csv
   pm4py.write.write_ocel2_xml
   pm4py.write.write_ocel2_sqlite
   pm4py.write.write_ocel2_json
   pm4py.convert
   pm4py.convert.convert_to_event_log
   pm4py.convert.convert_to_event_stream
   pm4py.convert.convert_to_dataframe
   pm4py.convert.convert_to_bpmn
   pm4py.convert.convert_to_petri_net
   pm4py.convert.convert_to_process_tree
   pm4py.convert.convert_to_reachability_graph
   pm4py.convert.convert_log_to_ocel
   pm4py.convert.convert_log_to_networkx
   pm4py.convert.convert_ocel_to_networkx
   pm4py.convert.convert_log_to_time_intervals
   pm4py.convert.convert_petri_net_to_networkx
   pm4py.convert.convert_petri_net_type
   pm4py.convert.convert_to_powl
   pm4py.discovery
   pm4py.discovery.discover_dfg
   pm4py.discovery.discover_directly_follows_graph
   pm4py.discovery.discover_dfg_typed
   pm4py.discovery.discover_performance_dfg
   pm4py.discovery.discover_petri_net_alpha
   pm4py.discovery.discover_petri_net_alpha_plus
   pm4py.discovery.discover_petri_net_inductive
   pm4py.discovery.discover_petri_net_heuristics
   pm4py.discovery.discover_petri_net_ilp
   pm4py.discovery.discover_petri_net_genetic
   pm4py.discovery.discover_process_tree_inductive
   pm4py.discovery.discover_heuristics_net
   pm4py.discovery.derive_minimum_self_distance
   pm4py.discovery.discover_footprints
   pm4py.discovery.discover_eventually_follows_graph
   pm4py.discovery.discover_bpmn_inductive
   pm4py.discovery.discover_bpmn_split_miner
   pm4py.discovery.discover_transition_system
   pm4py.discovery.discover_prefix_tree
   pm4py.discovery.discover_temporal_profile
   pm4py.discovery.discover_declare
   pm4py.discovery.discover_log_skeleton
   pm4py.discovery.discover_batches
   pm4py.discovery.discover_powl
   pm4py.discovery.correlation_miner
   pm4py.discovery.discover_otg
   pm4py.discovery.discover_etot
   pm4py.conformance
   pm4py.conformance.conformance_diagnostics_token_based_replay
   pm4py.conformance.conformance_diagnostics_alignments
   pm4py.conformance.conformance_diagnostics_footprints
   pm4py.conformance.fitness_token_based_replay
   pm4py.conformance.fitness_alignments
   pm4py.conformance.fitness_footprints
   pm4py.conformance.precision_token_based_replay
   pm4py.conformance.precision_alignments
   pm4py.conformance.precision_footprints
   pm4py.conformance.generalization_tbr
   pm4py.conformance.replay_prefix_tbr
   pm4py.conformance.check_is_fitting
   pm4py.conformance.conformance_temporal_profile
   pm4py.conformance.conformance_declare
   pm4py.conformance.conformance_log_skeleton
   pm4py.conformance.conformance_ocdfg
   pm4py.conformance.conformance_otg
   pm4py.conformance.conformance_etot
   pm4py.vis
   pm4py.vis.view_petri_net
   pm4py.vis.save_vis_petri_net
   pm4py.vis.view_performance_dfg
   pm4py.vis.save_vis_performance_dfg
   pm4py.vis.view_dfg
   pm4py.vis.save_vis_dfg
   pm4py.vis.view_process_tree
   pm4py.vis.save_vis_process_tree
   pm4py.vis.view_bpmn
   pm4py.vis.save_vis_bpmn
   pm4py.vis.view_heuristics_net
   pm4py.vis.save_vis_heuristics_net
   pm4py.vis.view_dotted_chart
   pm4py.vis.save_vis_dotted_chart
   pm4py.vis.view_sna
   pm4py.vis.save_vis_sna
   pm4py.vis.view_case_duration_graph
   pm4py.vis.save_vis_case_duration_graph
   pm4py.vis.view_events_per_time_graph
   pm4py.vis.save_vis_events_per_time_graph
   pm4py.vis.view_performance_spectrum
   pm4py.vis.save_vis_performance_spectrum
   pm4py.vis.view_events_distribution_graph
   pm4py.vis.save_vis_events_distribution_graph
   pm4py.vis.view_ocdfg
   pm4py.vis.save_vis_ocdfg
   pm4py.vis.view_ocpn
   pm4py.vis.save_vis_ocpn
   pm4py.vis.view_object_graph
   pm4py.vis.save_vis_object_graph
   pm4py.vis.view_network_analysis
   pm4py.vis.save_vis_network_analysis
   pm4py.vis.view_transition_system
   pm4py.vis.save_vis_transition_system
   pm4py.vis.view_prefix_tree
   pm4py.vis.save_vis_prefix_tree
   pm4py.vis.view_alignments
   pm4py.vis.save_vis_alignments
   pm4py.vis.view_footprints
   pm4py.vis.save_vis_footprints
   pm4py.vis.view_powl
   pm4py.vis.save_vis_powl
   pm4py.stats
   pm4py.stats.get_start_activities
   pm4py.stats.get_end_activities
   pm4py.stats.get_event_attributes
   pm4py.stats.get_trace_attributes
   pm4py.stats.get_event_attribute_values
   pm4py.stats.get_trace_attribute_values
   pm4py.stats.get_variants
   pm4py.stats.get_variants_as_tuples
   pm4py.stats.split_by_process_variant
   pm4py.stats.get_variants_paths_duration
   pm4py.stats.get_minimum_self_distances
   pm4py.stats.get_minimum_self_distance_witnesses
   pm4py.stats.get_case_arrival_average
   pm4py.stats.get_rework_cases_per_activity
   pm4py.stats.get_case_overlap
   pm4py.stats.get_cycle_time
   pm4py.stats.get_all_case_durations
   pm4py.stats.get_case_duration
   pm4py.stats.get_frequent_trace_segments
   pm4py.stats.get_service_time
   pm4py.stats.get_activity_position_summary
   pm4py.stats.get_process_cube
   pm4py.stats.get_stochastic_language
   pm4py.filtering
   pm4py.filtering.filter_log_relative_occurrence_event_attribute
   pm4py.filtering.filter_start_activities
   pm4py.filtering.filter_end_activities
   pm4py.filtering.filter_event_attribute_values
   pm4py.filtering.filter_trace_attribute_values
   pm4py.filtering.filter_variants
   pm4py.filtering.filter_directly_follows_relation
   pm4py.filtering.filter_eventually_follows_relation
   pm4py.filtering.filter_time_range
   pm4py.filtering.filter_between
   pm4py.filtering.filter_case_size
   pm4py.filtering.filter_case_performance
   pm4py.filtering.filter_activities_rework
   pm4py.filtering.filter_paths_performance
   pm4py.filtering.filter_variants_top_k
   pm4py.filtering.filter_variants_by_coverage_percentage
   pm4py.filtering.filter_prefixes
   pm4py.filtering.filter_suffixes
   pm4py.filtering.filter_trace_segments
   pm4py.filtering.filter_ocel_event_attribute
   pm4py.filtering.filter_ocel_object_attribute
   pm4py.filtering.filter_ocel_object_types_allowed_activities
   pm4py.filtering.filter_ocel_object_per_type_count
   pm4py.filtering.filter_ocel_start_events_per_object_type
   pm4py.filtering.filter_ocel_end_events_per_object_type
   pm4py.filtering.filter_ocel_events_timestamp
   pm4py.filtering.filter_four_eyes_principle
   pm4py.filtering.filter_activity_done_different_resources
   pm4py.filtering.filter_ocel_object_types
   pm4py.filtering.filter_ocel_events
   pm4py.filtering.filter_ocel_objects
   pm4py.filtering.filter_ocel_activities_connected_object_type
   pm4py.filtering.filter_ocel_cc_object
   pm4py.filtering.filter_ocel_cc_length
   pm4py.filtering.filter_ocel_cc_otype
   pm4py.filtering.filter_ocel_cc_activity
   pm4py.filtering.filter_dfg_activities_percentage
   pm4py.filtering.filter_dfg_paths_percentage
   pm4py.ml
   pm4py.ml.split_train_test
   pm4py.ml.get_prefixes_from_log
   pm4py.ml.extract_features_dataframe
   pm4py.ml.extract_temporal_features_dataframe
   pm4py.ml.extract_target_vector
   pm4py.ml.extract_outcome_enriched_dataframe
   pm4py.ml.extract_ocel_features
   pm4py.sim
   pm4py.sim.play_out
   pm4py.sim.generate_process_tree
   pm4py.ocel
   pm4py.ocel.ocel_get_object_types
   pm4py.ocel.ocel_get_attribute_names
   pm4py.ocel.ocel_flattening
   pm4py.ocel.ocel_object_type_activities
   pm4py.ocel.ocel_objects_ot_count
   pm4py.ocel.discover_ocdfg
   pm4py.ocel.discover_oc_petri_net
   pm4py.ocel.discover_objects_graph
   pm4py.ocel.ocel_temporal_summary
   pm4py.ocel.ocel_objects_summary
   pm4py.ocel.ocel_objects_interactions_summary
   pm4py.ocel.sample_ocel_objects
   pm4py.ocel.sample_ocel_connected_components
   pm4py.ocel.ocel_drop_duplicates
   pm4py.ocel.ocel_merge_duplicates
   pm4py.ocel.ocel_sort_by_additional_column
   pm4py.ocel.ocel_add_index_based_timedelta
   pm4py.ocel.ocel_o2o_enrichment
   pm4py.ocel.ocel_e2o_lifecycle_enrichment
   pm4py.ocel.cluster_equivalent_ocel
   pm4py.ocel.ocel_drill_down
   pm4py.ocel.ocel_roll_up
   pm4py.ocel.ocel_unfold
   pm4py.ocel.ocel_fold
   pm4py.llm
   pm4py.llm.openai_query
   pm4py.llm.google_query
   pm4py.llm.anthropic_query
   pm4py.llm.abstract_dfg
   pm4py.llm.abstract_variants
   pm4py.llm.abstract_ocel
   pm4py.llm.abstract_ocel_ocdfg
   pm4py.llm.abstract_ocel_features
   pm4py.llm.abstract_event_stream
   pm4py.llm.abstract_petri_net
   pm4py.llm.abstract_log_attributes
   pm4py.llm.abstract_log_features
   pm4py.llm.abstract_temporal_profile
   pm4py.llm.abstract_case
   pm4py.llm.abstract_declare
   pm4py.llm.abstract_log_skeleton
   pm4py.llm.clustering
   pm4py.llm.nlp_to_log_query
   pm4py.llm.nlp_to_log_filter
   pm4py.llm.automated_hypotheses_formulation
   pm4py.llm.explain_visualization
   pm4py.connectors
   pm4py.connectors.extract_log_outlook_mails
   pm4py.connectors.extract_log_outlook_calendar
   pm4py.connectors.extract_log_windows_events
   pm4py.connectors.extract_log_chrome_history
   pm4py.connectors.extract_log_firefox_history
   pm4py.connectors.extract_log_github
   pm4py.connectors.extract_log_camunda_workflow
   pm4py.connectors.extract_log_sap_o2c
   pm4py.connectors.extract_log_sap_accounting
   pm4py.connectors.extract_ocel_outlook_mails
   pm4py.connectors.extract_ocel_outlook_calendar
   pm4py.connectors.extract_ocel_windows_events
   pm4py.connectors.extract_ocel_chrome_history
   pm4py.connectors.extract_ocel_firefox_history
   pm4py.connectors.extract_ocel_github
   pm4py.connectors.extract_ocel_camunda_workflow
   pm4py.connectors.extract_ocel_sap_o2c
   pm4py.connectors.extract_ocel_sap_accounting
   pm4py.org
   pm4py.org.discover_handover_of_work_network
   pm4py.org.discover_working_together_network
   pm4py.org.discover_activity_based_resource_similarity
   pm4py.org.discover_subcontracting_network
   pm4py.org.discover_organizational_roles
   pm4py.org.discover_network_analysis
   pm4py.privacy
   pm4py.privacy.anonymize_differential_privacy
   pm4py.analysis
   pm4py.analysis.construct_synchronous_product_net
   pm4py.analysis.cluster_log
   pm4py.analysis.insert_case_service_waiting_time
   pm4py.analysis.insert_case_arrival_finish_rate
   pm4py.analysis.solve_marking_equation
   pm4py.analysis.solve_extended_marking_equation
   pm4py.analysis.check_is_sound
   pm4py.analysis.check_soundness
   pm4py.analysis.insert_artificial_start_end
   pm4py.analysis.check_is_workflow_net
   pm4py.analysis.maximal_decomposition
   pm4py.analysis.generate_marking
   pm4py.analysis.compute_emd
   pm4py.analysis.reduce_petri_net_invisibles
   pm4py.analysis.reduce_petri_net_implicit_places
   pm4py.analysis.get_enabled_transitions
   pm4py.analysis.simplicity_petri_net
   pm4py.analysis.behavioral_similarity
   pm4py.analysis.structural_similarity
   pm4py.analysis.embeddings_similarity
   pm4py.analysis.get_activity_labels
   pm4py.analysis.replace_activity_labels
   pm4py.analysis.label_sets_similarity
   pm4py.analysis.map_labels_from_second_model
   pm4py.utils
   pm4py.utils.is_polars_lazyframe
   pm4py.utils.rebase
   pm4py.utils.parse_process_tree
   pm4py.utils.parse_powl_model_string
   pm4py.utils.format_dataframe
   pm4py.utils.serialize
   pm4py.utils.deserialize
   pm4py.utils.get_properties
   pm4py.utils.set_classifier
   pm4py.utils.parse_event_log_string
   pm4py.utils.project_on_event_attribute
   pm4py.utils.sample_cases
   pm4py.utils.sample_events

.. toctree::
   :hidden:
   :maxdepth: 2

   api/pm4py.algo
   api/pm4py.objects
   api/pm4py.statistics
   api/pm4py.streaming
   api/pm4py.util
   api/pm4py.visualization
   api/pm4py.analysis
   api/pm4py.cli
   api/pm4py.conformance
   api/pm4py.connectors
   api/pm4py.convert
   api/pm4py.discovery
   api/pm4py.filtering
   api/pm4py.hof
   api/pm4py.llm
   api/pm4py.meta
   api/pm4py.ml
   api/pm4py.ocel
   api/pm4py.org
   api/pm4py.privacy
   api/pm4py.read
   api/pm4py.sim
   api/pm4py.stats
   api/pm4py.utils
   api/pm4py.vis
   api/pm4py.write
