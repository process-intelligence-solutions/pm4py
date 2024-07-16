import inspect
import os
import sys
import traceback
import importlib.util


EXECUTE_EXAMPLES = True


def inductive_miner_dfg_lc():
    from examples import inductive_miner_dfg_lc
    print("\n\ninductive_miner_dfg_lc")
    inductive_miner_dfg_lc.execute_script()


def bpmn_js_visualization():
    from examples import bpmn_js_visualization
    print("\n\nbpmn_js_visualization")
    bpmn_js_visualization.execute_script()


def log_projection_dfg_variant():
    from examples import log_projection_dfg_variant
    print("\n\nlog_projection_dfg_variant")
    log_projection_dfg_variant.execute_script()


def streaming_live_to_static_stream():
    from examples import streaming_live_to_static_stream
    print("\n\nstreaming_live_to_static_stream")
    streaming_live_to_static_stream.execute_script()


def declare_simple():
    from examples import declare_simple
    print("\n\ndeclare_simple")
    declare_simple.execute_script()


def variants_paths_duration():
    from examples import variants_paths_duration
    print("\n\nvariants_paths_duration")
    variants_paths_duration.execute_script()


def ev_to_obj_types_graph():
    from examples import ev_to_obj_types_graph
    print("\n\nev_to_obj_types_graph")
    ev_to_obj_types_graph.execute_script()


def label_splitting():
    from examples import label_splitting
    print("\n\nlabel_splitting")
    label_splitting.execute_script()


def nx_ocel_to_graphviz():
    from examples import nx_ocel_to_graphviz
    print("\n\nnx_ocel_to_graphviz")
    nx_ocel_to_graphviz.execute_script()


def nx_traditional_to_graphviz():
    from examples import nx_traditional_to_graphviz
    print("\n\nnx_traditional_to_graphviz")
    nx_traditional_to_graphviz.execute_script()


def segments_retrieval_filtering():
    from examples import segments_retrieval_filtering
    print("\n\nsegments_retrieval_filtering")
    segments_retrieval_filtering.execute_script()


def feature_extraction_case_loc():
    from examples import feature_extraction_case_loc
    print("\n\nfeature_extraction_case_loc")
    feature_extraction_case_loc.execute_script()


def powl_discovery():
    from examples import powl_discovery
    print("\n\npowl_discovery")
    powl_discovery.execute_script()


def powl_parsing():
    from examples import powl_parsing
    print("\n\npowl_parsing")
    powl_parsing.execute_script()

def log_skeleton_manual_constraints():
    from examples import log_skeleton_manual_constraints
    print("\n\nlog_skeleton_manual_constraints")
    log_skeleton_manual_constraints.execute_script()


def stochastic_petri_playout():
    from examples import stochastic_petri_playout
    print("\n\nstochastic_petri_playout")
    stochastic_petri_playout.execute_script()


def trace_attrib_hierarch_cluster():
    from examples import trace_attrib_hierarch_cluster
    print("\n\ntrace_attrib_hierarch_cluster")
    trace_attrib_hierarch_cluster.execute_script()


def activities_to_alphabet():
    from examples import activities_to_alphabet
    print("\n\nactivities_to_alphabet")
    activities_to_alphabet.execute_script()


def ocel_filter_cc():
    from examples import ocel_filter_cc
    print("\n\nocel_filter_cc")
    ocel_filter_cc.execute_script()


def queue_check_exponential():
    from examples import queue_check_exponential
    print("\n\nqueue_check_exponential")
    queue_check_exponential.execute_script()


def queue_check_max_conc_exec():
    from examples import queue_check_max_conc_exec
    print("\n\nqueue_check_max_conc_exec")
    queue_check_max_conc_exec.execute_script()


def timestamp_granularity():
    from examples import timestamp_granularity
    print("\n\ntimestamp_granularity")
    timestamp_granularity.execute_script()


def ocel_occm_example():
    from examples import ocel_occm_example
    print("\n\nocel_occm_example")
    ocel_occm_example.execute_script()


def ocel_clustering():
    from examples import ocel_clustering
    print("\n\nocel_clustering")
    ocel_clustering.execute_script()


def ocel_enrichment():
    from examples import ocel_enrichment
    print("\n\nocel_enrichment")
    ocel_enrichment.execute_script()


def validation_ocel20_xml():
    from examples import validation_ocel20_xml
    print("\n\nvalidation_ocel20_xml")
    validation_ocel20_xml.execute_script()


def consecutive_act_case_grouping_filter():
    from examples import consecutive_act_case_grouping_filter
    print("\n\nconsecutive_act_case_grouping_filter")
    consecutive_act_case_grouping_filter.execute_script()


def cost_based_dfg():
    from examples import cost_based_dfg
    print("\n\ncost_based_dfg")
    cost_based_dfg.execute_script()


def df_to_log_postpro():
    from examples import df_to_log_postpro
    print("\n\ndf_to_log_postpro")
    df_to_log_postpro.execute_script()


def hybrid_ilp_miner():
    from examples import hybrid_ilp_miner
    print("\n\nhybrid_ilp_miner")
    hybrid_ilp_miner.execute_script()


def ml_insert_case_arrival_finish():
    from examples import ml_insert_case_arrival_finish
    print("\n\nml_insert_case_arrival_finish")
    ml_insert_case_arrival_finish.execute_script()


def ml_insert_waiting_service_time():
    from examples import ml_insert_waiting_service_time
    print("\n\nml_insert_waiting_service_time")
    ml_insert_waiting_service_time.execute_script()


def ml_log_to_target_vector():
    from examples import ml_log_to_target_vectory
    print("\n\nml_log_to_target_vector")
    ml_log_to_target_vectory.execute_script()


def ml_outcome_enriched():
    from examples import ml_outcome_enriched
    print("\n\nml_outcome_enriched")
    ml_outcome_enriched.execute_script()


def ocel20_import_export():
    from examples import ocel20_import_export
    print("\n\nocel20_import_export")
    ocel20_import_export.execute_script()


def revised_playout():
    from examples import revised_playout
    print("\n\nrevised_playout")
    revised_playout.execute_script()


def timestamp_case_grouping_filter():
    from examples import timestamp_case_grouping_filter
    print("\n\ntimestamp_case_grouping_filter")
    timestamp_case_grouping_filter.execute_script()


def trace_clustering():
    from examples import trace_clustering
    print("\n\ntrace_clustering")
    trace_clustering.execute_script()


def validation_ocel20_relational():
    from examples import validation_ocel20_relational
    print("\n\nvalidation_ocel20_relation")
    validation_ocel20_relational.execute_script()


def all_optimal_alignments():
    from examples import all_optimal_alignments
    print("\n\nall_optimal_alignments")
    all_optimal_alignments.execute_script()


def inductive_miner():
    from examples import inductive_miner
    print("\n\ninductive_miner")
    inductive_miner.execute_script()


def inductive_miner_dfg():
    from examples import inductive_miner_dfg
    print("\n\ninductive_miner_dfg")
    inductive_miner_dfg.execute_script()


def inductive_miner_variants():
    from examples import inductive_miner_variants
    print("\n\ninductive_miner_variants")
    inductive_miner_variants.execute_script()


def heu_miner_plus_plus():
    from examples import heuminer_plusplus
    print("\n\nheuminer_plusplus")
    heuminer_plusplus.execute_script()


def interval_events_overlap():
    from examples import interval_events_overlap
    print("\n\ninterval_events_overlap")
    interval_events_overlap.execute_script()


def kneighb_regression():
    from examples import kneighb_regression
    print("\n\nkneighb_regression")
    kneighb_regression.execute_script()


def log_to_int_tree_open_paths():
    from examples import log_to_int_tree_open_paths
    print("\n\nlog_to_int_tree_open_paths")
    log_to_int_tree_open_paths.execute_script()


def murata_reduction():
    from examples import murata_reduction
    print("\n\nmurata_reduction")
    murata_reduction.execute_script()


def ocel_merge_duplicates():
    from examples import ocel_merge_duplicates
    print("\n\nocel_merge_duplicates")
    ocel_merge_duplicates.execute_script()


def ocel_saw_net_disc():
    from examples import ocel_saw_net_disc
    print("\n\nocel_saw_net_disc")
    ocel_saw_net_disc.execute_script()


def ocel_to_nx():
    from examples import ocel_to_nx
    print("\n\nocel_to_nx")
    ocel_to_nx.execute_script()


def saw_net_ocel_multi():
    from examples import saw_net_ocel_multi
    print("\n\nsaw_net_ocel_multi")
    saw_net_ocel_multi.execute_script()


def saw_net_ocel_single():
    from examples import saw_net_ocel_single
    print("\n\nsaw_net_ocel_single")
    saw_net_ocel_single.execute_script()


def temporal_features():
    from examples import temporal_features
    print("\n\ntemporal_features")
    temporal_features.execute_script()


def transform_db_to_ocel():
    from examples import transform_db_to_ocel
    print("\n\ntransform_db_to_ocel")
    transform_db_to_ocel.execute_script()


def transform_db_to_ocel_2():
    from examples import transform_db_to_ocel_2
    print("\n\ntransform_db_to_ocel_2")
    transform_db_to_ocel_2.execute_script()


def transform_db_to_xes():
    from examples import transform_db_to_xes
    print("\n\ntransform_db_to_xes")
    transform_db_to_xes.execute_script()


def trie():
    from examples import trie
    print("\n\ntrie")
    trie.execute_script()


def feature_extraction_ocel():
    from examples import feature_extraction_ocel
    print("\n\nfeature_extraction_ocel")
    feature_extraction_ocel.execute_script()


def ocel_validation():
    from examples import ocel_validation
    print("\n\nocel_validation")
    ocel_validation.execute_script()


def process_tree_frequency_annotation():
    from examples import process_tree_frequency_annotation
    print("\n\nprocess_tree_frequency_annotation")
    process_tree_frequency_annotation.execute_script()


def tree_manual_generation():
    from examples import tree_manual_generation
    print("\n\ntree_manual_generation")
    tree_manual_generation.execute_script()


def workalendar_example():
    from examples import workalendar_example
    print("\n\nworkalendar_example")
    workalendar_example.execute_script()


def merging_case_relations():
    from examples import merging_case_relations
    print("\n\nmerging_case_relations")
    merging_case_relations.execute_script()


def activity_position():
    from examples import activity_position
    print("\n\nactivity_position")
    activity_position.execute_script()


def link_analysis_vbfa():
    from examples import link_analysis_vbfa
    print("\n\nlink_analysis_vbfa")
    link_analysis_vbfa.execute_script()


def ocel_streaming():
    from examples import ocel_streaming
    print("\n\nocel_streaming")
    ocel_streaming.execute_script()


def petri_manual_generation():
    from examples import petri_manual_generation
    print("\n\npetri_manual_generation")
    petri_manual_generation.execute_script()


def timestamp_interleavings():
    from examples import timestamp_interleavings
    print("\n\ntimestamp_interleavings")
    timestamp_interleavings.execute_script()


def object_centric_petri_net_discovery():
    from examples import object_centric_petri_net_discovery
    print("\n\nobject_centric_petri_net_discovery")
    object_centric_petri_net_discovery.execute_script()


def trans_system_stochastic_view():
    from examples import trans_system_stochastic_vis
    print("\n\ntrans_system_stochastic_view")
    trans_system_stochastic_vis.execute_script()


def network_analysis():
    from examples import network_analysis
    print("\n\nnetwork_analysis")
    network_analysis.execute_script()


def read_write_ocel():
    from examples import read_write_ocel
    print("\n\nread_write_ocel")
    read_write_ocel.execute_script()


def ocdfg_discovery():
    from examples import ocdfg_discovery
    print("\n\nocdfg_discovery")
    ocdfg_discovery.execute_script()


def enrich_log_with_align():
    from examples import enrich_log_with_align
    print("\n\nenrich_log_with_align")
    enrich_log_with_align.execute_script()


def extended_marking_equation():
    from examples import extended_marking_equation
    print("\n\nextended_marking_equation")
    extended_marking_equation.execute_script()


def features_locally_linear_embedding():
    from examples import features_locally_linear_embedding
    print("\n\nfeatures_locally_linear_embedding")
    features_locally_linear_embedding.execute_script()


def discovery_data_petri_net():
    from examples import discovery_data_petri_net
    print("\n\ndiscovery_data_petri_net")
    discovery_data_petri_net.execute_script()


def performance_dfg_simulation():
    from examples import performance_dfg_simulation
    print("\n\nperformance_dfg_simulation")
    performance_dfg_simulation.execute_script()


def data_petri_nets():
    from examples import data_petri_nets
    print("\n\ndata_petri_nets")
    data_petri_nets.execute_script()


def inhibitor_reset_arcs():
    from examples import inhibitor_reset_arcs
    print("\n\ninhibitor_reset_arcs")
    inhibitor_reset_arcs.execute_script()


def batch_detection():
    from examples import batch_detection
    print("\n\nbatch_detection")
    batch_detection.execute_script()


def case_overlap_stat():
    from examples import case_overlap_stat
    print("\n\ncase_overlap_stat")
    case_overlap_stat.execute_script()


def cycle_time():
    from examples import cycle_time
    print("\n\ncycle_time")
    cycle_time.execute_script()


def rework():
    from examples import rework
    print("\n\nrework")
    rework.execute_script()


def events_distribution():
    from examples import events_distribution
    print("\n\nevents_distribution")
    events_distribution.execute_script()


def dotted_chart():
    from examples import dotted_chart
    print("\n\ndotted_chart")
    dotted_chart.execute_script()


def performance_spectrum():
    from examples import perf_spectrum_visualization
    print("\n\nperformance_spectrum")
    perf_spectrum_visualization.execute_script()


def woflan():
    from examples import woflan
    print("\n\nwoflan")
    woflan.execute_script()


def bpmn_from_pt():
    from examples import bpmn_from_pt_conversion
    print("\n\nbpmn_from_pt_conversion")
    bpmn_from_pt_conversion.execute_script()


def bpmn_import_and_to_petri_net():
    from examples import bpmn_import_and_to_petri_net
    print("\n\nbpmn_import_and_to_petri_net")
    bpmn_import_and_to_petri_net.execute_script()


def tree_playout():
    from examples import tree_playout
    print("\n\ntree_playout")
    tree_playout.execute_script()


def emd_evaluation():
    from examples import emd_evaluation
    print("\n\nemd_evaluation")
    emd_evaluation.execute_script()


def footprints_tree_conf():
    from examples import footprints_tree_conf
    print("\n\nfootprints_tree_conf")
    footprints_tree_conf.execute_script()


def simplified_interface():
    from examples import simplified_interface
    print("\n\nsimplified_interface")
    simplified_interface.execute_script()


def footprints_petri_net():
    from examples import footprints_petri_net
    print("\n\nfootprints_petri_net")
    footprints_petri_net.execute_script()


def corr_mining():
    from examples import corr_mining
    print("\n\ncorr_mining")
    corr_mining.execute_script()


def log_skeleton():
    from examples import log_skeleton
    print("\n\nlog_skeleton")
    log_skeleton.execute_script()


def roles_detection():
    from examples import roles_detection
    print("\n\nroles_detection")
    roles_detection.execute_script()


def alignment_test():
    from examples import alignment_test
    print("\n\nalignment_test")
    alignment_test.execute_script()


def dec_treplay_imdf():
    from examples import dec_treplay_imdf
    print("\n\ndec_treplay_imdf")
    dec_treplay_imdf.execute_script()


def logs_petri_visual_comparison():
    from examples import logs_petri_visual_comparison
    print("\n\nlogs_petri_visual_comparison")
    logs_petri_visual_comparison.execute_script()


def imdf_example():
    from examples import im_example
    print("\n\nimdf_example")
    im_example.execute_script()


def test_evaluation():
    from examples import test_evaluation
    print("\n\ntestEvaluation")
    test_evaluation.execute_script()


def sna_log():
    from examples import sna_log
    print("\n\nsna_log")
    sna_log.execute_script()


def token_replay_alpha():
    from examples import token_replay_alpha
    print("\n\ntokenReplay_alpha")
    token_replay_alpha.execute_script()


def manual_log_generation():
    from examples import manual_log_generation
    print("\n\nmanual_log_generation")
    manual_log_generation.execute_script()


def token_replay_imdf():
    from examples import token_replay_imdf
    print("\n\ntokenReplay_imdf")
    token_replay_imdf.execute_script()


def decisiontree_trivial_example():
    from examples import decisiontree_trivial_example
    print("\n\ndecisiontree_trivial_example")
    decisiontree_trivial_example.execute_script()


def decisiontree_align_example():
    from examples import decisiontree_align_example
    print("\n\ndecisiontree_align_example")
    decisiontree_align_example.execute_script()


def align_decomposition_example():
    from examples import align_decomposition_example
    print("\n\nalign_decomposition_example")
    align_decomposition_example.execute_script()


def transition_system_test():
    from examples import transition_system_test
    print("\n\ntransition_system_test")
    transition_system_test.execute_script()


def heu_miner_test():
    from examples import heu_miner_test
    print("\n\nheu_miner_test")
    heu_miner_test.execute_script()


def dfg_min_ex_log():
    from examples import dfg_min_ex_log
    print("\n\ndfg_min_ex_log")
    dfg_min_ex_log.execute_script()


def dfg_min_ex_pandas():
    from examples import dfg_min_ex_pandas
    print("\n\ndfg_min_ex_pandas")
    dfg_min_ex_pandas.execute_script()


def dfg_filt_act_paths_perc():
    from examples import dfg_filt_act_paths_perc
    print("\n\ndfg_filt_act_paths_perc")
    dfg_filt_act_paths_perc.execute_script()


def graphs_visualization():
    from examples import graphs_visualization
    print("\n\ngraphs_visualization")
    graphs_visualization.execute_script()


def backwards_token_replay():
    from examples import backwards_token_replay
    print("\n\nbackwards_token_replay")
    backwards_token_replay.execute_script()


def transient_dfg():
    from examples import transient_dfg
    print("\n\ntransient_dfg")
    transient_dfg.execute_script()


def transient_petri_net():
    from examples import transient_petri_net
    print("\n\ntransient_petri_net")
    transient_petri_net.execute_script()


def monte_carlo_dfg():
    from examples import montecarlo_dfg
    print("\n\nmontecarlo_dfg")
    montecarlo_dfg.execute_script()


def monte_carlo_petri_net():
    from examples import montecarlo_petri_net
    print("\n\nmontecarlo_petri_net")
    montecarlo_petri_net.execute_script()


def visualization_processtree():
    from examples import visualization_processtree
    print("\n\nvisualization_processtree")
    visualization_processtree.execute_script()


def diagn_add_dataframe():
    from examples import diagn_add_dataframe
    print("\n\ndiagn_add_dataframe")
    diagn_add_dataframe.execute_script()


def pn_to_pt():
    from examples import pn_to_pt
    print("\n\npn_to_pt")
    pn_to_pt.execute_script()


def visualization_align_table():
    from examples import visualization_align_table
    print("\n\nvisualization_align_table")
    visualization_align_table.execute_script()


def align_approx_pt():
    from examples import align_approx_pt
    print("\n\nalign_approx_pt")
    align_approx_pt.execute_script()


def streaming_conformance_footprints():
    from examples import streaming_conformance_footprints
    print("\n\nstreaming_conformance_footprints")
    streaming_conformance_footprints.execute_script()


def streaming_conformance_tbr():
    from examples import streaming_conformance_tbr
    print("\n\nstreaming_conformance_tbr")
    streaming_conformance_tbr.execute_script()


def streaming_conformance_temporal_profile():
    from examples import streaming_conformance_temporal_profile
    print("\n\nstreaming_conformance_temporal_profile")
    streaming_conformance_temporal_profile.execute_script()


def streaming_csv_reader_event_stream():
    from examples import streaming_csv_reader_event_stream
    print("\n\nstreaming_csv_reader_event_stream")
    streaming_csv_reader_event_stream.execute_script()


def streaming_discovery_dfg():
    from examples import streaming_discovery_dfg
    print("\n\nstreaming_discovery_dfg")
    streaming_discovery_dfg.execute_script()


def streaming_xes_reader_event_stream():
    from examples import streaming_xes_reader_event_stream
    print("\n\nstreaming_xes_reader_event_stream")
    streaming_xes_reader_event_stream.execute_script()


def streaming_xes_reader_trace_stream():
    from examples import streaming_xes_reader_trace_stream
    print("\n\nstreaming_xes_reader_trace_stream")
    streaming_xes_reader_trace_stream.execute_script()


def example_check_fitness():
    from examples import example_check_fitness
    print("\n\nexample_check_fitness")
    example_check_fitness.execute_script()


def dfg_align_log():
    from examples import dfg_align_log
    print("\n\ndfg_align_log")
    dfg_align_log.execute_script()


def dfg_playout():
    from examples import dfg_playout
    print("\n\ndfg_playout")
    dfg_playout.execute_script()


def temporal_profile_log():
    from examples import temporal_profile_log
    print("\n\ntemporal_profile_log")
    temporal_profile_log.execute_script()


def temporal_profile_dataframe():
    from examples import temporal_profile_dataframe
    print("\n\ntemporal_profile_dataframe")
    temporal_profile_dataframe.execute_script()


def dataframe_prefix_and_fea_extraction():
    from examples import dataframe_prefix_and_fea_extraction
    print("\n\ndataframe_prefix_and_fea_extraction")
    dataframe_prefix_and_fea_extraction.execute_script()


def logs_alignments():
    from examples import logs_alignment
    print("\n\nlogs_alignment")
    logs_alignment.execute_script()


def orgmining_local_diagn():
    from examples import orgmining_local_diagn
    print("\n\norgmining_local_diagn")
    orgmining_local_diagn.execute_script()


def resource_profiles_log():
    from examples import resource_profiles_log
    print("\n\nresource_profiles_log")
    resource_profiles_log.execute_script()


def resource_profile_pandas():
    from examples import resource_profiles_pandas
    print("\n\nresource_profile_pandas")
    resource_profiles_pandas.execute_script()


def process_tree_reduction():
    from examples import process_tree_reduction
    print("\n\nprocess_tree_reduction")
    process_tree_reduction.execute_script()


def execute_script(f):
    try:
        f()
    except ImportError:
        import time
        traceback.print_exc()
        time.sleep(3)
    except KeyError:
        import time
        traceback.print_exc()
        time.sleep(3)
    except:
        traceback.print_exc()
        input("\npress INPUT if you want to continue")


def main():
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))

    import pm4py
    import numpy
    import pandas
    import networkx

    pm4py.util.constants.SHOW_PROGRESS_BAR = True
    pm4py.util.constants.SHOW_EVENT_LOG_DEPRECATION = False
    pm4py.util.constants.SHOW_INTERNAL_WARNINGS = False
    #pm4py.util.constants.DEFAULT_TIMESTAMP_PARSE_FORMAT = None

    if EXECUTE_EXAMPLES:
        execute_script(inductive_miner_dfg_lc)
        execute_script(log_projection_dfg_variant)
        execute_script(streaming_live_to_static_stream)
        execute_script(powl_discovery)
        execute_script(powl_parsing)
        execute_script(ev_to_obj_types_graph)
        execute_script(label_splitting)
        execute_script(nx_ocel_to_graphviz)
        execute_script(nx_traditional_to_graphviz)
        execute_script(segments_retrieval_filtering)
        execute_script(stochastic_petri_playout)
        execute_script(simplified_interface)
        execute_script(bpmn_js_visualization)
        execute_script(read_write_ocel)
        execute_script(discovery_data_petri_net)
        execute_script(data_petri_nets)
        execute_script(inhibitor_reset_arcs)
        execute_script(logs_petri_visual_comparison)
        execute_script(align_decomposition_example)
        execute_script(ocdfg_discovery)
        execute_script(woflan)
        execute_script(inductive_miner)
        execute_script(inductive_miner_dfg)
        execute_script(inductive_miner_variants)
        execute_script(heu_miner_plus_plus)
        execute_script(activities_to_alphabet)
        execute_script(ocel_filter_cc)
        execute_script(queue_check_exponential)
        execute_script(queue_check_max_conc_exec)
        execute_script(timestamp_granularity)
        execute_script(ocel_occm_example)
        execute_script(ocel_clustering)
        execute_script(ocel_enrichment)
        execute_script(validation_ocel20_xml)
        execute_script(consecutive_act_case_grouping_filter)
        execute_script(cost_based_dfg)
        execute_script(df_to_log_postpro)
        execute_script(hybrid_ilp_miner)
        execute_script(ml_insert_case_arrival_finish)
        execute_script(ml_insert_waiting_service_time)
        execute_script(ml_log_to_target_vector)
        execute_script(ml_outcome_enriched)
        execute_script(ocel20_import_export)
        execute_script(revised_playout)
        execute_script(timestamp_case_grouping_filter)
        execute_script(trace_clustering)
        execute_script(validation_ocel20_relational)
        execute_script(interval_events_overlap)
        execute_script(kneighb_regression)
        execute_script(log_to_int_tree_open_paths)
        execute_script(murata_reduction)
        execute_script(ocel_merge_duplicates)
        execute_script(ocel_saw_net_disc)
        execute_script(ocel_to_nx)
        execute_script(saw_net_ocel_multi)
        execute_script(saw_net_ocel_single)
        execute_script(temporal_features)
        execute_script(transform_db_to_ocel)
        execute_script(transform_db_to_xes)
        execute_script(transform_db_to_ocel_2)
        execute_script(feature_extraction_ocel)
        execute_script(ocel_validation)
        execute_script(process_tree_frequency_annotation)
        execute_script(tree_manual_generation)
        execute_script(workalendar_example)
        execute_script(merging_case_relations)
        execute_script(activity_position)
        execute_script(link_analysis_vbfa)
        execute_script(ocel_streaming)
        execute_script(petri_manual_generation)
        #execute_script(timestamp_interleavings)
        execute_script(object_centric_petri_net_discovery)
        execute_script(trans_system_stochastic_view)
        execute_script(network_analysis)
        execute_script(enrich_log_with_align)
        execute_script(extended_marking_equation)
        execute_script(features_locally_linear_embedding)
        execute_script(dotted_chart)
        execute_script(performance_spectrum)
        execute_script(orgmining_local_diagn)
        execute_script(resource_profiles_log)
        execute_script(resource_profile_pandas)
        execute_script(process_tree_reduction)
        execute_script(dataframe_prefix_and_fea_extraction)
        execute_script(logs_alignments)
        execute_script(bpmn_from_pt)
        execute_script(bpmn_import_and_to_petri_net)
        execute_script(tree_playout)
        execute_script(emd_evaluation)
        execute_script(footprints_tree_conf)
        execute_script(footprints_petri_net)
        execute_script(corr_mining)
        execute_script(log_skeleton)
        execute_script(roles_detection)
        execute_script(alignment_test)
        execute_script(dec_treplay_imdf)
        execute_script(imdf_example)
        execute_script(test_evaluation)
        execute_script(sna_log)
        execute_script(token_replay_alpha)
        execute_script(manual_log_generation)
        execute_script(token_replay_imdf)
        execute_script(decisiontree_trivial_example)
        execute_script(decisiontree_align_example)
        execute_script(transition_system_test)
        execute_script(heu_miner_test)
        execute_script(dfg_min_ex_log)
        execute_script(dfg_min_ex_pandas)
        execute_script(graphs_visualization)
        execute_script(backwards_token_replay)
        execute_script(transient_dfg)
        execute_script(transient_petri_net)
        execute_script(example_check_fitness)
        execute_script(pn_to_pt)
        execute_script(align_approx_pt)
        execute_script(visualization_processtree)
        execute_script(visualization_align_table)
        execute_script(declare_simple)
        execute_script(variants_paths_duration)
        execute_script(feature_extraction_case_loc)
        execute_script(log_skeleton_manual_constraints)
        execute_script(trace_attrib_hierarch_cluster)
        execute_script(streaming_conformance_footprints)
        execute_script(streaming_conformance_tbr)
        execute_script(streaming_csv_reader_event_stream)
        execute_script(streaming_discovery_dfg)
        execute_script(streaming_xes_reader_event_stream)
        execute_script(streaming_xes_reader_trace_stream)
        execute_script(monte_carlo_dfg)
        execute_script(monte_carlo_petri_net)

    print("numpy version: "+str(numpy.__version__))
    print("pandas version: "+str(pandas.__version__))
    print("networkx version: "+str(networkx.__version__))

    if importlib.util.find_spec("scipy"):
        import scipy
        print("scipy version: "+str(scipy.__version__))

    if importlib.util.find_spec("lxml"):
        import lxml
        print("lxml version: "+str(lxml.__version__))

    if importlib.util.find_spec("matplotlib"):
        import matplotlib
        print("matplotlib version: "+str(matplotlib.__version__))

    if importlib.util.find_spec("sklearn"):
        import sklearn
        print("sklearn version: "+str(sklearn.__version__))

    print("pm4py version: "+str(pm4py.__version__))
    print("Python version: "+str(sys.version))


if __name__ == "__main__":
    main()
