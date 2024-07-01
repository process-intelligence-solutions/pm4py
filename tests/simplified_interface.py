import importlib.util
import os
import unittest

import pm4py
from pm4py.objects.bpmn.obj import BPMN
from pm4py.objects.petri_net.obj import PetriNet
from pm4py.objects.process_tree.obj import ProcessTree
from pm4py.util import constants, pandas_utils
from pm4py.objects.log.util import dataframe_utils
from pm4py.objects.log.importer.xes import importer as xes_importer


class SimplifiedInterfaceTest(unittest.TestCase):
    def test_csv(self):
        df = pandas_utils.read_csv("input_data/running-example.csv")
        df = dataframe_utils.convert_timestamp_columns_in_df(df, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["time:timestamp"])
        df["case:concept:name"] = df["case:concept:name"].astype("string")

        log2 = pm4py.convert_to_event_log(df)
        stream1 = pm4py.convert_to_event_stream(log2)
        df2 = pm4py.convert_to_dataframe(log2)
        pm4py.write_xes(log2, "test_output_data/log.xes")
        os.remove("test_output_data/log.xes")

    def test_alpha_miner(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            net, im, fm = pm4py.discover_petri_net_alpha(log)

    def test_alpha_miner_plus(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            net, im, fm = pm4py.discover_petri_net_alpha_plus(log)

    def test_inductive_miner(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            net, im, fm = pm4py.discover_petri_net_inductive(log)

    def test_inductive_miner_noise(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            net, im, fm = pm4py.discover_petri_net_inductive(log, noise_threshold=0.5)

    def test_heuristics_miner(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            net, im, fm = pm4py.discover_petri_net_heuristics(log)

    def test_inductive_miner_tree(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            tree = pm4py.discover_process_tree_inductive(log)
            tree = pm4py.discover_process_tree_inductive(log, noise_threshold=0.2)

    def test_heuristics_miner_heu_net(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            heu_net = pm4py.discover_heuristics_net(log)

    def test_dfg(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            dfg, sa, ea = pm4py.discover_directly_follows_graph(log)

    def test_read_petri(self):
        net, im, fm = pm4py.read_pnml("input_data/running-example.pnml")

    def test_read_tree(self):
        tree = pm4py.read_ptml("input_data/running-example.ptml")

    def test_read_dfg(self):
        dfg, sa, ea = pm4py.read_dfg("input_data/running-example.dfg")

    def test_alignments_simpl_interface(self):
        for legacy_obj in [True, False]:
            for diagn_df in [True, False]:
                log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
                net, im, fm = pm4py.discover_petri_net_inductive(log)
                aligned_traces = pm4py.conformance_diagnostics_alignments(log, net, im, fm, return_diagnostics_dataframe=diagn_df)

    def test_tbr_simpl_interface(self):
        for legacy_obj in [True, False]:
            for diagn_df in [True, False]:
                log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
                net, im, fm = pm4py.discover_petri_net_inductive(log)
                replayed_traces = pm4py.conformance_diagnostics_token_based_replay(log, net, im, fm, return_diagnostics_dataframe=diagn_df)

    def test_fitness_alignments(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            net, im, fm = pm4py.discover_petri_net_inductive(log)
            fitness_ali = pm4py.fitness_alignments(log, net, im, fm)

    def test_fitness_tbr(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            net, im, fm = pm4py.discover_petri_net_inductive(log)
            fitness_tbr = pm4py.fitness_token_based_replay(log, net, im, fm)

    def test_precision_alignments(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            net, im, fm = pm4py.discover_petri_net_inductive(log)
            precision_ali = pm4py.precision_alignments(log, net, im, fm)

    def test_precision_tbr(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            net, im, fm = pm4py.discover_petri_net_inductive(log)
            precision_tbr = pm4py.precision_token_based_replay(log, net, im, fm)

    def test_convert_to_tree_from_petri(self):
        net, im, fm = pm4py.read_pnml("input_data/running-example.pnml")
        tree = pm4py.convert_to_process_tree(net, im, fm)
        self.assertTrue(isinstance(tree, ProcessTree))

    def test_convert_to_tree_from_bpmn(self):
        bpmn = pm4py.read_bpmn("input_data/running-example.bpmn")
        tree = pm4py.convert_to_process_tree(bpmn)
        self.assertTrue(isinstance(tree, ProcessTree))

    def test_convert_to_net_from_tree(self):
        tree = pm4py.read_ptml("input_data/running-example.ptml")
        net, im, fm = pm4py.convert_to_petri_net(tree)
        self.assertTrue(isinstance(net, PetriNet))

    def test_convert_to_net_from_bpmn(self):
        bpmn = pm4py.read_bpmn("input_data/running-example.bpmn")
        net, im, fm = pm4py.convert_to_petri_net(bpmn)
        self.assertTrue(isinstance(net, PetriNet))

    def test_convert_to_net_from_dfg(self):
        dfg, sa, ea = pm4py.read_dfg("input_data/running-example.dfg")
        net, im, fm = pm4py.convert_to_petri_net(dfg, sa, ea)
        self.assertTrue(isinstance(net, PetriNet))

    def test_convert_to_net_from_heu(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            heu_net = pm4py.discover_heuristics_net(log)
            net, im, fm = pm4py.convert_to_petri_net(heu_net)
            self.assertTrue(isinstance(net, PetriNet))

    def test_convert_to_bpmn_from_tree(self):
        tree = pm4py.read_ptml("input_data/running-example.ptml")
        bpmn = pm4py.convert_to_bpmn(tree)
        self.assertTrue(isinstance(bpmn, BPMN))

    def test_statistics_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.get_start_activities(log)
            pm4py.get_end_activities(log)
            pm4py.get_event_attributes(log)
            pm4py.get_trace_attributes(log)
            pm4py.get_event_attribute_values(log, "org:resource")
            pm4py.get_variants_as_tuples(log)

    def test_statistics_df(self):
        df = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        df = dataframe_utils.convert_timestamp_columns_in_df(df, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        df["CaseID"] = df["CaseID"].astype("string")

        pm4py.get_start_activities(df, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")
        pm4py.get_end_activities(df, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")
        pm4py.get_event_attributes(df)
        pm4py.get_event_attribute_values(df, "Resource", case_id_key="CaseID")
        pm4py.get_variants_as_tuples(df, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")

    def test_playout(self):
        net, im, fm = pm4py.read_pnml("input_data/running-example.pnml")
        pm4py.play_out(net, im, fm)

    def test_generator(self):
        pm4py.generate_process_tree()

    def test_mark_em_equation(self):
        for legacy_obj in [True, False]:
            log = xes_importer.apply("input_data/running-example.xes")
            net, im, fm = pm4py.read_pnml("input_data/running-example.pnml")
            sync_net, sync_im, sync_fm = pm4py.construct_synchronous_product_net(log[0], net, im, fm)
            m_h = pm4py.solve_marking_equation(sync_net, sync_im, sync_fm)
            em_h = pm4py.solve_extended_marking_equation(log[0], sync_net, sync_im, sync_fm)

    def test_new_statistics_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.get_trace_attribute_values(log, "case:creator")
            pm4py.discover_eventually_follows_graph(log)
            pm4py.get_case_arrival_average(log)

    def test_new_statistics_df(self):
        df = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        df = dataframe_utils.convert_timestamp_columns_in_df(df, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT,
                                                             timest_columns=["Timestamp"])
        df["CaseID"] = df["CaseID"].astype("string")

        pm4py.discover_eventually_follows_graph(df, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")
        pm4py.get_case_arrival_average(df, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")

    def test_serialization_log(self):
        if importlib.util.find_spec("pyarrow"):
            for legacy_obj in [True, False]:
                log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
                ser = pm4py.serialize(log)
                log2 = pm4py.deserialize(ser)

    def test_serialization_dataframe(self):
        if importlib.util.find_spec("pyarrow"):
            df = pandas_utils.read_csv("input_data/running-example.csv")
            df = dataframe_utils.convert_timestamp_columns_in_df(df, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["time:timestamp"])
            ser = pm4py.serialize(df)
            df2 = pm4py.deserialize(ser)

    def test_serialization_petri_net(self):
        net, im, fm = pm4py.read_pnml("input_data/running-example.pnml")
        ser = pm4py.serialize(net, im, fm)
        net2, im2, fm2 = pm4py.deserialize(ser)

    def test_serialization_process_tree(self):
        tree = pm4py.read_ptml("input_data/running-example.ptml")
        ser = pm4py.serialize(tree)
        tree2 = pm4py.deserialize(ser)

    def test_serialization_bpmn(self):
        bpmn = pm4py.read_bpmn("input_data/running-example.bpmn")
        ser = pm4py.serialize(bpmn)
        bpmn2 = pm4py.deserialize(ser)

    def test_serialization_dfg(self):
        dfg, sa, ea = pm4py.read_dfg("input_data/running-example.dfg")
        ser = pm4py.serialize(dfg, sa, ea)
        dfg2, sa2, ea2 = pm4py.deserialize(ser)

    def test_minimum_self_distance(self):
        import pm4py
        for legacy_obj in [True, False]:
            log = pm4py.read_xes(os.path.join("input_data", "running-example.xes"), return_legacy_log_object=legacy_obj)
            msd = pm4py.get_minimum_self_distances(log)

    def test_minimum_self_distance_2(self):
        import pm4py
        for legacy_obj in [True, False]:
            log = pm4py.read_xes(os.path.join("input_data", "running-example.xes"), return_legacy_log_object=legacy_obj)
            msd = pm4py.get_minimum_self_distance_witnesses(log)

    def test_marking_equation_net(self):
        import pm4py
        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))
        net, im, fm = pm4py.discover_petri_net_inductive(log)
        pm4py.solve_marking_equation(net, im, fm)

    def test_marking_equation_sync_net(self):
        import pm4py
        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))
        net, im, fm = pm4py.discover_petri_net_inductive(log)
        sync_net, sync_im, sync_fm = pm4py.construct_synchronous_product_net(log[0], net, im, fm)
        res = pm4py.solve_marking_equation(sync_net, sync_im, sync_fm)
        self.assertIsNotNone(res)
        self.assertEqual(res, 11)

    def test_ext_marking_equation_sync_net(self):
        import pm4py
        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))
        net, im, fm = pm4py.discover_petri_net_inductive(log)
        sync_net, sync_im, sync_fm = pm4py.construct_synchronous_product_net(log[0], net, im, fm)
        res = pm4py.solve_extended_marking_equation(log[0], sync_net, sync_im, sync_fm)
        self.assertIsNotNone(res)

    def test_alignments_tree_simpl_interface(self):
        import pm4py
        for legacy_obj in [True, False]:
            for diagn_df in [True, False]:
                log = pm4py.read_xes(os.path.join("input_data", "running-example.xes"), return_legacy_log_object=legacy_obj)
                tree = pm4py.read_ptml(os.path.join("input_data", "running-example.ptml"))
                res = pm4py.conformance_diagnostics_alignments(log, tree, return_diagnostics_dataframe=diagn_df)
                self.assertIsNotNone(res)

    def test_alignments_dfg_simpl_interface(self):
        import pm4py
        for legacy_obj in [True, False]:
            for diagn_df in [True, False]:
                log = pm4py.read_xes(os.path.join("input_data", "running-example.xes"), return_legacy_log_object=legacy_obj)
                dfg, sa, ea = pm4py.read_dfg(os.path.join("input_data", "running-example.dfg"))
                res = pm4py.conformance_diagnostics_alignments(log, dfg, sa, ea, return_diagnostics_dataframe=diagn_df)
                self.assertIsNotNone(res)

    def test_alignments_bpmn_simpl_interface(self):
        import pm4py
        for legacy_obj in [True, False]:
            for diagn_df in [True, False]:
                log = pm4py.read_xes(os.path.join("input_data", "running-example.xes"), return_legacy_log_object=legacy_obj)
                bpmn_graph = pm4py.read_bpmn(os.path.join("input_data", "running-example.bpmn"))
                res = pm4py.conformance_diagnostics_alignments(log, bpmn_graph, return_diagnostics_dataframe=diagn_df)
                self.assertIsNotNone(res)

    def test_discovery_inductive_bpmn(self):
        import pm4py
        for legacy_obj in [True, False]:
            log = pm4py.read_xes(os.path.join("input_data", "running-example.xes"), return_legacy_log_object=legacy_obj)
            bpmn_graph = pm4py.discover_bpmn_inductive(log)
            self.assertIsNotNone(bpmn_graph)

    def test_generation(self):
        import pm4py
        tree = pm4py.generate_process_tree()
        self.assertIsNotNone(tree)

    def test_play_out_tree(self):
        import pm4py
        tree = pm4py.read_ptml(os.path.join("input_data", "running-example.ptml"))
        log = pm4py.play_out(tree)

    def test_play_out_net(self):
        import pm4py
        net, im, fm = pm4py.read_pnml(os.path.join("input_data", "running-example.pnml"))
        log = pm4py.play_out(net, im, fm)

    def test_msd(self):
        import pm4py
        for legacy_obj in [True, False]:
            log = pm4py.read_xes(os.path.join("input_data", "running-example.xes"), return_legacy_log_object=legacy_obj)
            res1 = pm4py.get_minimum_self_distance_witnesses(log)
            res2 = pm4py.get_minimum_self_distances(log)
            self.assertIsNotNone(res1)
            self.assertIsNotNone(res2)

    def test_case_arrival(self):
        import pm4py
        for legacy_obj in [True, False]:
            log = pm4py.read_xes(os.path.join("input_data", "running-example.xes"), return_legacy_log_object=legacy_obj)
            avg = pm4py.get_case_arrival_average(log)
            self.assertIsNotNone(avg)

    def test_efg(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.discover_eventually_follows_graph(log)

    def test_write_pnml(self):
        net, im, fm = pm4py.read_pnml("input_data/running-example.pnml")
        pm4py.write_pnml(net, im, fm, "test_output_data/running-example.pnml")
        os.remove("test_output_data/running-example.pnml")

    def test_write_ptml(self):
        process_tree = pm4py.read_ptml("input_data/running-example.ptml")
        pm4py.write_ptml(process_tree, "test_output_data/running-example.ptml")
        os.remove("test_output_data/running-example.ptml")

    def test_write_dfg(self):
        dfg, sa, ea = pm4py.read_dfg("input_data/running-example.dfg")
        pm4py.write_dfg(dfg, sa, ea, "test_output_data/running-example.dfg")
        os.remove("test_output_data/running-example.dfg")

    def test_write_bpmn(self):
        bpmn_graph = pm4py.read_bpmn("input_data/running-example.bpmn")
        pm4py.write_bpmn(bpmn_graph, "test_output_data/running-example.bpmn")
        os.remove("test_output_data/running-example.bpmn")

    def test_rebase(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        df = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        dataframe = pm4py.rebase(dataframe, activity_key="Activity", case_id="CaseID", timestamp_key="Timestamp", timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT)

    def test_parse_process_tree(self):
        tree = pm4py.parse_process_tree("-> ( 'a', X ( 'b', 'c' ), tau )")

    def test_parse_log_string(self):
        elog = pm4py.parse_event_log_string(["A,B,C", "A,B,D"])

    def test_project_eattr(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            lst = pm4py.project_on_event_attribute(log, "org:resource")

    def test_sample_cases_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.sample_cases(log, 2)

    def test_sample_cases_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.sample_cases(dataframe, 2, case_id_key="CaseID")

    def test_sample_events_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.sample_events(log, 2)

    def test_sample_events_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.sample_events(dataframe, 2)

    def test_check_soundness(self):
        net, im, fm = pm4py.read_pnml("input_data/running-example.pnml")
        self.assertTrue(pm4py.check_soundness(net, im, fm))

    def test_check_wfnet(self):
        net, im, fm = pm4py.read_pnml("input_data/running-example.pnml")
        self.assertTrue(pm4py.check_is_workflow_net(net))

    def test_artificial_start_end_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.insert_artificial_start_end(log)

    def test_artificial_start_end_dataframe(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.insert_artificial_start_end(dataframe, activity_key="Activity", timestamp_key="Timestamp", case_id_key="CaseID")

    def test_hof_filter_log(self):
        log = xes_importer.apply("input_data/running-example.xes")
        pm4py.filter_log(log, lambda x: len(x) > 5)

    def test_hof_filter_trace(self):
        log = xes_importer.apply("input_data/running-example.xes")
        pm4py.filter_trace(log[0], lambda x: x["concept:name"] == "decide")

    def test_hof_sort_log(self):
        log = xes_importer.apply("input_data/running-example.xes")
        pm4py.sort_log(log, key=lambda x: x.attributes["concept:name"])

    def test_hof_sort_trace(self):
        log = xes_importer.apply("input_data/running-example.xes")
        pm4py.sort_trace(log[0], key=lambda x: x["concept:name"])

    def test_split_train_test_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.split_train_test(log, train_percentage=0.6)

    def test_split_train_test_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.split_train_test(dataframe, train_percentage=0.6, case_id_key="CaseID")

    def test_get_prefixes_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.get_prefixes_from_log(log, 3)

    def test_get_prefixes_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.get_prefixes_from_log(dataframe, 3, case_id_key="CaseID")

    def test_convert_reachab(self):
        net, im, fm = pm4py.read_pnml("input_data/running-example.pnml")
        ts = pm4py.convert_to_reachability_graph(net, im, fm)

    def test_hw_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.discover_handover_of_work_network(log)

    def test_hw_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.discover_handover_of_work_network(dataframe, resource_key="Resource", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_wt_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.discover_working_together_network(log)

    def test_wt_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.discover_working_together_network(dataframe, resource_key="Resource", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_act_based_res_sim_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.discover_activity_based_resource_similarity(log)

    def test_act_based_res_sim_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.discover_activity_based_resource_similarity(dataframe, activity_key="Activity", resource_key="Resource", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_subcontracting_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.discover_subcontracting_network(log)

    def test_subcontracting_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.discover_subcontracting_network(dataframe, resource_key="Resource", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_roles_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.discover_organizational_roles(log)

    def test_roles_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.discover_organizational_roles(dataframe, activity_key="Activity", resource_key="Resource", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_network_analysis_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.discover_network_analysis(log, "case:concept:name", "case:concept:name", "org:resource", "org:resource", "concept:name")

    def test_network_analysis_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.discover_network_analysis(dataframe, "CaseID", "CaseID", "Resource", "Resource", "Activity", sorting_column="Timestamp", timestamp_column="Timestamp")

    def test_discover_batches_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.discover_batches(log)

    def test_discover_batches_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.discover_batches(dataframe, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp", resource_key="Resource")

    def test_log_skeleton_log_simplified_interface(self):
        for legacy_obj in [True, False]:
            for diagn_df in [True, False]:
                log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
                model = pm4py.discover_log_skeleton(log)
                pm4py.conformance_log_skeleton(log, model, return_diagnostics_dataframe=diagn_df)

    def test_log_skeleton_df_simplified_interface(self):
        for diagn_df in [True, False]:
            dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
            dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe,
                                                                        timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT,
                                                                        timest_columns=["Timestamp"])
            dataframe["CaseID"] = dataframe["CaseID"].astype("string")

            model = pm4py.discover_log_skeleton(dataframe, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")
            pm4py.conformance_log_skeleton(dataframe, model, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp", return_diagnostics_dataframe=diagn_df)

    def test_temporal_profile_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            model = pm4py.discover_temporal_profile(log)
            pm4py.conformance_temporal_profile(log, model)

    def test_temporal_profile_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        model = pm4py.discover_temporal_profile(dataframe, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")
        pm4py.conformance_temporal_profile(dataframe, model, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_ocel_get_obj_types(self):
        ocel = pm4py.read_ocel("input_data/ocel/example_log.csv")
        pm4py.ocel_get_object_types(ocel)

    def test_ocel_get_attr_names(self):
        ocel = pm4py.read_ocel("input_data/ocel/example_log.csv")
        pm4py.ocel_get_attribute_names(ocel)

    def test_ocel_flattening(self):
        ocel = pm4py.read_ocel("input_data/ocel/example_log.csv")
        pm4py.ocel_flattening(ocel, "order")
    def test_stats_var_tuples_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.get_variants_as_tuples(dataframe, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_stats_cycle_time_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.get_cycle_time(log)

    def test_stats_cycle_time_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.get_cycle_time(dataframe, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_stats_case_durations_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.get_all_case_durations(log)

    def test_stats_case_durations_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.get_all_case_durations(dataframe, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_stats_case_duration_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.get_case_duration(log, "1")

    def test_stats_case_duration_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.get_case_duration(dataframe, "1", activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_stats_act_pos_summary_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.get_activity_position_summary(log, "check ticket")

    def test_stats_act_pos_summary_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.get_activity_position_summary(dataframe, "check ticket", activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_filter_act_done_diff_res_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_activity_done_different_resources(log, "check ticket")

    def test_filter_act_done_diff_res_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_activity_done_different_resources(dataframe, "check ticket", activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp", resource_key="Resource")

    def test_filter_four_eyes_principle_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_four_eyes_principle(log, "register request", "check ticket")

    def test_filter_four_eyes_principle_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_four_eyes_principle(dataframe, "register request", "check ticket", activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp", resource_key="Resource")

    def test_filter_rel_occ_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_log_relative_occurrence_event_attribute(log, 0.8, level="cases")

    def test_filter_rel_occ_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_log_relative_occurrence_event_attribute(dataframe, 0.8, attribute_key="Activity", level="cases", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_filter_start_activities_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_start_activities(log, ["register request"])

    def test_filter_start_activities_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_start_activities(dataframe, ["register request"], activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_filter_end_activities_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_end_activities(log, ["pay compensation"])

    def test_filter_end_activities_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_end_activities(dataframe, ["pay compensation"], activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_filter_eve_attr_values_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_event_attribute_values(log, "concept:name", ["register request", "pay compensation", "reject request"])

    def test_filter_eve_attr_values_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_event_attribute_values(dataframe, "Activity", ["register request", "pay compensation", "reject request"], case_id_key="CaseID")

    def test_filter_trace_attr_values_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_trace_attribute_values(log, "case:creator", ["Fluxicon"])

    def test_filter_variant_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_variants(log, [('register request', 'examine casually', 'check ticket', 'decide', 'reinitiate request', 'examine thoroughly', 'check ticket', 'decide', 'pay compensation')])

    def test_filter_variant_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_variants(dataframe, [('register request', 'examine casually', 'check ticket', 'decide', 'reinitiate request', 'examine thoroughly', 'check ticket', 'decide', 'pay compensation')], activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_filter_dfg_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_directly_follows_relation(log, [("register request", "check ticket")])

    def test_filter_dfg_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_directly_follows_relation(dataframe, [("register request", "check ticket")], activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_filter_efg_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_eventually_follows_relation(log, [("register request", "check ticket")])

    def test_filter_efg_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_eventually_follows_relation(dataframe, [("register request", "check ticket")], activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_filter_time_range_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_time_range(log, "2009-01-01 01:00:00", "2011-01-01 01:00:00")

    def test_filter_time_range_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_time_range(dataframe, "2009-01-01 01:00:00", "2011-01-01 01:00:00", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_filter_between_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_between(log, "check ticket", "decide")

    def test_filter_between_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_between(dataframe, "check ticket", "decide", activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_filter_case_size_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_case_size(log, 10, 20)

    def test_filter_case_size_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_case_size(dataframe, 10, 20, case_id_key="CaseID")

    def test_filter_case_performance_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_case_performance(log, 86400, 8640000)

    def test_filter_case_performance_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_case_performance(dataframe, 86400, 8640000, case_id_key="CaseID", timestamp_key="Timestamp")

    def test_filter_activities_rework_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_activities_rework(log, "check ticket")

    def test_filter_act_rework_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_activities_rework(dataframe, "check ticket", activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_filter_paths_perf_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_paths_performance(log, ("register request", "check ticket"), 86400, 864000)

    def test_filter_paths_perf_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_paths_performance(dataframe, ("register request", "check ticket"), 86400, 864000, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_filter_vars_top_k_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_variants_top_k(log, 1)

    def test_filter_vars_top_k_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_variants_top_k(dataframe, 1, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_filter_vars_coverage(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_variants_by_coverage_percentage(log, 0.1)

    def test_filter_vars_coverage(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_variants_by_coverage_percentage(dataframe, 0.1, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_filter_prefixes_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_prefixes(log, "check ticket")

    def test_filter_prefixes_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_prefixes(dataframe, "check ticket", activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_filter_suffixes_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.filter_suffixes(log, "check ticket")

    def test_filter_suffixes_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.filter_suffixes(dataframe, "check ticket", activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_discover_perf_dfg_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.discover_performance_dfg(log)

    def test_discover_perf_dfg_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.discover_performance_dfg(dataframe, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_discover_footprints_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.discover_footprints(log)

    def test_discover_ts_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.discover_transition_system(log)

    def test_discover_ts_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.discover_transition_system(dataframe, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_discover_pref_tree_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.discover_prefix_tree(log)

    def test_discover_pref_tree_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.discover_prefix_tree(dataframe, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")

    def test_discover_ocpn(self):
        ocel = pm4py.read_ocel("input_data/ocel/example_log.csv")
        pm4py.discover_oc_petri_net(ocel)

    def test_conformance_alignments_pn_log_simplified_interface(self):
        for legacy_obj in [True, False]:
            for diagn_df in [True, False]:
                log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
                net, im, fm = pm4py.discover_petri_net_inductive(log)
                pm4py.conformance_diagnostics_alignments(log, net, im, fm, return_diagnostics_dataframe=diagn_df)

    def test_conformance_alignments_pn_df_simplified_interface(self):
        for diagn_df in [True, False]:
            dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
            dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe,
                                                                        timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT,
                                                                        timest_columns=["Timestamp"])
            dataframe["CaseID"] = dataframe["CaseID"].astype("string")

            net, im, fm = pm4py.discover_petri_net_inductive(dataframe, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")
            pm4py.conformance_diagnostics_alignments(dataframe, net, im, fm, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp", return_diagnostics_dataframe=diagn_df)

    def test_conformance_diagnostics_fp_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            tree = pm4py.discover_process_tree_inductive(log)
            pm4py.conformance_diagnostics_footprints(log, tree)

    def test_fitness_fp_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            tree = pm4py.discover_process_tree_inductive(log)
            pm4py.fitness_footprints(log, tree)

    def test_precision_fp_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            tree = pm4py.discover_process_tree_inductive(log)
            pm4py.precision_footprints(log, tree)

    def test_maximal_decomposition(self):
        net, im, fm = pm4py.read_pnml("input_data/running-example.pnml")
        pm4py.maximal_decomposition(net, im, fm)

    def test_fea_ext_log(self):
        for legacy_obj in [True, False]:
            log = pm4py.read_xes("input_data/running-example.xes", return_legacy_log_object=legacy_obj)
            pm4py.extract_features_dataframe(log)

    def test_fea_ext_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        pm4py.extract_features_dataframe(dataframe, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp", resource_key="Resource")

    def test_new_alpha_miner_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")
        pm4py.discover_petri_net_alpha(dataframe, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")

    def test_new_heu_miner_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")
        pm4py.discover_petri_net_heuristics(dataframe, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")

    def test_new_dfg_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")
        pm4py.discover_dfg(dataframe, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")

    def test_new_perf_dfg_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")
        pm4py.discover_performance_dfg(dataframe, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")

    def test_new_tbr_df_simpl_interface(self):
        for ret_df in [True, False]:
            dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
            dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe,
                                                                        timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT,
                                                                        timest_columns=["Timestamp"])
            dataframe["CaseID"] = dataframe["CaseID"].astype("string")
            net, im, fm = pm4py.discover_petri_net_inductive(dataframe, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")
            pm4py.conformance_diagnostics_token_based_replay(dataframe, net, im, fm, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp", return_diagnostics_dataframe=ret_df)

    def test_new_tbr_fitness_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")
        net, im, fm = pm4py.discover_petri_net_inductive(dataframe, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")
        pm4py.fitness_token_based_replay(dataframe, net, im, fm, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")

    def test_new_tbr_precision_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")
        net, im, fm = pm4py.discover_petri_net_inductive(dataframe, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")
        pm4py.precision_token_based_replay(dataframe, net, im, fm, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")

    def test_new_align_df_simpl_interface(self):
        for diagn_df in [True, False]:
            dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
            dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe,
                                                                        timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT,
                                                                        timest_columns=["Timestamp"])
            dataframe["CaseID"] = dataframe["CaseID"].astype("string")
            net, im, fm = pm4py.discover_petri_net_inductive(dataframe, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")
            pm4py.conformance_diagnostics_alignments(dataframe, net, im, fm, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp", return_diagnostics_dataframe=diagn_df)

    def test_new_align_fitness_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")
        net, im, fm = pm4py.discover_petri_net_inductive(dataframe, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")
        pm4py.fitness_alignments(dataframe, net, im, fm, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")

    def test_new_align_precision_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")
        net, im, fm = pm4py.discover_petri_net_inductive(dataframe, case_id_key="CaseID", activity_key="Activity",
                                                         timestamp_key="Timestamp")
        pm4py.precision_alignments(dataframe, net, im, fm, case_id_key="CaseID", activity_key="Activity", timestamp_key="Timestamp")

    def test_vis_case_duration_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")

        if importlib.util.find_spec("matplotlib"):
            target = os.path.join("test_output_data", "case_duration.svg")
            pm4py.save_vis_case_duration_graph(dataframe, target, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")
            os.remove(target)

    def test_vis_ev_distr_graph_df(self):
        dataframe = pandas_utils.read_csv("input_data/running-example-transformed.csv")
        dataframe = dataframe_utils.convert_timestamp_columns_in_df(dataframe, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT, timest_columns=["Timestamp"])
        dataframe["CaseID"] = dataframe["CaseID"].astype("string")
        target = os.path.join("test_output_data", "ev_distr_graph.svg")

        if importlib.util.find_spec("matplotlib"):
            pm4py.save_vis_events_distribution_graph(dataframe, target, activity_key="Activity", case_id_key="CaseID", timestamp_key="Timestamp")
            os.remove(target)

    def test_ocel_object_graph(self):
        ocel = pm4py.read_ocel("input_data/ocel/example_log.jsonocel")
        ev_graph = pm4py.discover_objects_graph(ocel, graph_type="object_interaction")
        ev_graph = pm4py.discover_objects_graph(ocel, graph_type="object_descendants")
        ev_graph = pm4py.discover_objects_graph(ocel, graph_type="object_inheritance")
        ev_graph = pm4py.discover_objects_graph(ocel, graph_type="object_cobirth")
        ev_graph = pm4py.discover_objects_graph(ocel, graph_type="object_codeath")

    def test_ocel_temporal_summary(self):
        ocel = pm4py.read_ocel("input_data/ocel/example_log.jsonocel")
        temp_summary = pm4py.ocel_temporal_summary(ocel)

    def test_ocel_objects_summary(self):
        ocel = pm4py.read_ocel("input_data/ocel/example_log.jsonocel")
        objects_summary = pm4py.ocel_objects_summary(ocel)

    def test_ocel_filtering_ev_ids(self):
        ocel = pm4py.read_ocel("input_data/ocel/example_log.jsonocel")
        filtered_ocel = pm4py.filter_ocel_events(ocel, ["e1"])

    def test_ocel_filtering_obj_ids(self):
        ocel = pm4py.read_ocel("input_data/ocel/example_log.jsonocel")
        filtered_ocel = pm4py.filter_ocel_objects(ocel, ["o1"], level=1)
        filtered_ocel = pm4py.filter_ocel_objects(ocel, ["o1"], level=2)

    def test_ocel_filtering_obj_types(self):
        ocel = pm4py.read_ocel("input_data/ocel/example_log.jsonocel")
        filtered_ocel = pm4py.filter_ocel_object_types(ocel, ["order"])

    def test_ocel_filtering_cc(self):
        ocel = pm4py.read_ocel("input_data/ocel/example_log.jsonocel")
        filtered_ocel = pm4py.filter_ocel_cc_object(ocel, "o1")

    def test_ocel_drop_duplicates(self):
        ocel = pm4py.read_ocel("input_data/ocel/example_log.jsonocel")
        filtered_ocel = pm4py.ocel_drop_duplicates(ocel)

    def test_ocel_add_index_based_timedelta(self):
        ocel = pm4py.read_ocel("input_data/ocel/example_log.jsonocel")
        filtered_ocel = pm4py.ocel_add_index_based_timedelta(ocel)

    def test_ocel2_xml(self):
        ocel = pm4py.read_ocel2("input_data/ocel/ocel20_example.xmlocel")
        pm4py.write_ocel2(ocel, "test_output_data/ocel20_example.xmlocel")
        os.remove("test_output_data/ocel20_example.xmlocel")

    def test_ocel2_sqlite(self):
        ocel = pm4py.read_ocel2("input_data/ocel/ocel20_example.sqlite")
        pm4py.write_ocel2(ocel, "test_output_data/ocel20_example.sqlite")
        os.remove("test_output_data/ocel20_example.sqlite")


if __name__ == "__main__":
    unittest.main()
