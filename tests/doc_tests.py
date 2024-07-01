from pm4py.objects.log.util import dataframe_utils
import unittest
import importlib.util
import os
from pm4py.util import constants, pandas_utils
from pm4py.objects.conversion.process_tree import converter as process_tree_converter


class DocTests(unittest.TestCase):
    def load_running_example_xes(self):
        from pm4py.objects.log.importer.xes import importer
        log = importer.apply(os.path.join("input_data", "running-example.xes"))
        return log

    def load_running_example_df(self):
        df = pandas_utils.read_csv(os.path.join("input_data", "running-example.csv"))
        df = dataframe_utils.convert_timestamp_columns_in_df(df, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT)
        return df

    def load_running_example_stream(self):
        from pm4py.objects.conversion.log import converter
        df = pandas_utils.read_csv(os.path.join("input_data", "running-example.csv"))
        df = dataframe_utils.convert_timestamp_columns_in_df(df, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT)
        stream = converter.apply(df, variant=converter.TO_EVENT_STREAM)
        return stream

    def load_running_example_pnml(self):
        from pm4py.objects.petri_net.importer import importer
        net, im, fm = importer.apply(os.path.join("input_data", "running-example.pnml"))
        return net, im, fm

    def load_receipt_xes(self):
        from pm4py.objects.log.importer.xes import importer
        log = importer.apply(os.path.join("input_data", "receipt.xes"))
        return log

    def load_receipt_df(self):
        df = pandas_utils.read_csv(os.path.join("input_data", "receipt.csv"))
        df = dataframe_utils.convert_timestamp_columns_in_df(df, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT)
        return df

    def load_receipt_stream(self):
        from pm4py.objects.conversion.log import converter
        df = pandas_utils.read_csv(os.path.join("input_data", "receipt.csv"))
        df = dataframe_utils.convert_timestamp_columns_in_df(df, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT)
        stream = converter.apply(df, variant=converter.TO_EVENT_STREAM)
        return stream

    def load_roadtraffic50_xes(self):
        from pm4py.objects.log.importer.xes import importer
        log = importer.apply(os.path.join("input_data", "roadtraffic50traces.xes"))
        return log

    def load_roadtraffic100_xes(self):
        from pm4py.objects.log.importer.xes import importer
        log = importer.apply(os.path.join("input_data", "roadtraffic100traces.xes"))
        return log

    def load_roadtraffic100_csv(self):
        from pm4py.objects.log.importer.xes import importer
        log = importer.apply(os.path.join("input_data", "roadtraffic100traces.csv"))
        return log

    def test_1(self):
        from pm4py.objects.log.importer.xes import importer as xes_importer
        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))

    def test_2(self):
        from pm4py.objects.log.importer.xes import importer as xes_importer
        variant = xes_importer.Variants.ITERPARSE
        parameters = {variant.value.Parameters.TIMESTAMP_SORT: True}
        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"),
                                 variant=variant, parameters=parameters)

    def test_3(self):
        from pm4py.objects.conversion.log import converter as log_converter

        log_csv = pandas_utils.read_csv(os.path.join("input_data", "running-example.csv"), sep=',')
        event_log = log_converter.apply(log_csv, variant=log_converter.Variants.TO_EVENT_LOG)

    def test_4(self):
        from pm4py.objects.conversion.log import converter as log_converter

        log_csv = pandas_utils.read_csv(os.path.join("input_data", "running-example.csv"), sep=',')
        log_csv = log_csv.rename(columns={'case:concept:name': 'case'})
        parameters = {log_converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY: 'case'}
        event_log = log_converter.apply(log_csv, parameters=parameters, variant=log_converter.Variants.TO_EVENT_LOG)

    def test_5(self):
        log = self.load_running_example_xes()
        from pm4py.objects.log.exporter.xes import exporter as xes_exporter
        path = os.path.join("test_output_data", "ru.xes")
        xes_exporter.apply(log, path)
        os.remove(path)

    def test_6(self):
        log = self.load_running_example_xes()
        from pm4py.objects.conversion.log import converter as log_converter
        dataframe = log_converter.apply(log, variant=log_converter.Variants.TO_DATA_FRAME)
        dataframe.to_csv("ru.csv")
        os.remove("ru.csv")

    def test_8(self):
        from pm4py.algo.filtering.log.timestamp import timestamp_filter
        log = self.load_running_example_xes()
        filtered_log = timestamp_filter.filter_traces_contained(log, "2011-03-09 00:00:00", "2012-01-18 23:59:59")

    def test_9(self):
        from pm4py.algo.filtering.pandas.timestamp import timestamp_filter
        dataframe = self.load_running_example_df()
        df_timest_intersecting = timestamp_filter.filter_traces_intersecting(dataframe, "2011-03-09 00:00:00",
                                                                             "2012-01-18 23:59:59", parameters={
                timestamp_filter.Parameters.CASE_ID_KEY: "case:concept:name",
                timestamp_filter.Parameters.TIMESTAMP_KEY: "time:timestamp"})

    def test_10(self):
        from pm4py.algo.filtering.log.timestamp import timestamp_filter
        log = self.load_running_example_xes()
        filtered_log = timestamp_filter.filter_traces_intersecting(log, "2011-03-09 00:00:00", "2012-01-18 23:59:59")

    def test_11(self):
        from pm4py.algo.filtering.pandas.timestamp import timestamp_filter
        dataframe = self.load_running_example_df()
        df_timest_intersecting = timestamp_filter.filter_traces_intersecting(dataframe, "2011-03-09 00:00:00",
                                                                             "2012-01-18 23:59:59", parameters={
                timestamp_filter.Parameters.CASE_ID_KEY: "case:concept:name",
                timestamp_filter.Parameters.TIMESTAMP_KEY: "time:timestamp"})

    def test_12(self):
        from pm4py.algo.filtering.log.timestamp import timestamp_filter
        log = self.load_running_example_xes()
        filtered_log_events = timestamp_filter.apply_events(log, "2011-03-09 00:00:00", "2012-01-18 23:59:59")

    def test_13(self):
        from pm4py.algo.filtering.pandas.timestamp import timestamp_filter
        dataframe = self.load_running_example_df()
        df_timest_events = timestamp_filter.apply_events(dataframe, "2011-03-09 00:00:00", "2012-01-18 23:59:59",
                                                         parameters={
                                                             timestamp_filter.Parameters.CASE_ID_KEY: "case:concept:name",
                                                             timestamp_filter.Parameters.TIMESTAMP_KEY: "time:timestamp"})

    def test_14(self):
        from pm4py.algo.filtering.log.cases import case_filter
        log = self.load_running_example_xes()
        filtered_log = case_filter.filter_case_performance(log, 86400, 864000)

    def test_15(self):
        from pm4py.algo.filtering.pandas.cases import case_filter
        dataframe = self.load_running_example_df()
        df_cases = case_filter.filter_case_performance(dataframe, min_case_performance=86400,
                                                       max_case_performance=864000, parameters={
                case_filter.Parameters.CASE_ID_KEY: "case:concept:name",
                case_filter.Parameters.TIMESTAMP_KEY: "time:timestamp"})

    def test_22(self):
        from pm4py.algo.filtering.log.variants import variants_filter
        log = self.load_running_example_xes()
        variants = variants_filter.get_variants(log)

    def test_23(self):
        from pm4py.statistics.traces.generic.pandas import case_statistics
        df = self.load_running_example_df()
        variants = case_statistics.get_variants_df(df,
                                                   parameters={
                                                       case_statistics.Parameters.CASE_ID_KEY: "case:concept:name",
                                                       case_statistics.Parameters.ACTIVITY_KEY: "concept:name"})

    def test_24(self):
        from pm4py.statistics.traces.generic.log import case_statistics
        log = self.load_running_example_xes()
        variants_count = case_statistics.get_variant_statistics(log)
        variants_count = sorted(variants_count, key=lambda x: x['count'], reverse=True)

    def test_25(self):
        from pm4py.statistics.traces.generic.pandas import case_statistics
        df = self.load_running_example_df()
        variants_count = case_statistics.get_variant_statistics(df,
                                                                parameters={
                                                                    case_statistics.Parameters.CASE_ID_KEY: "case:concept:name",
                                                                    case_statistics.Parameters.ACTIVITY_KEY: "concept:name",
                                                                    case_statistics.Parameters.TIMESTAMP_KEY: "time:timestamp"})
        variants_count = sorted(variants_count, key=lambda x: x['case:concept:name'], reverse=True)

    def test_26(self):
        from pm4py.algo.filtering.log.variants import variants_filter
        log = self.load_running_example_xes()
        variants = ["register request,examine thoroughly,check ticket,decide,reject request"]
        filtered_log1 = variants_filter.apply(log, variants)

    def test_27(self):
        from pm4py.algo.filtering.pandas.variants import variants_filter
        df = self.load_running_example_df()
        variants = ["register request,examine thoroughly,check ticket,decide,reject request"]
        filtered_df1 = variants_filter.apply(df, variants,
                                             parameters={variants_filter.Parameters.CASE_ID_KEY: "case:concept:name",
                                                         variants_filter.Parameters.ACTIVITY_KEY: "concept:name"})

    def test_28(self):
        from pm4py.algo.filtering.log.variants import variants_filter
        log = self.load_running_example_xes()
        variants = ["register request,examine thoroughly,check ticket,decide,reject request"]
        filtered_log2 = variants_filter.apply(log, variants, parameters={variants_filter.Parameters.POSITIVE: False})

    def test_29(self):
        from pm4py.algo.filtering.pandas.variants import variants_filter
        df = self.load_running_example_df()
        variants = ["register request,examine thoroughly,check ticket,decide,reject request"]
        filtered_df2 = variants_filter.apply(df, variants,
                                             parameters={variants_filter.Parameters.POSITIVE: False,
                                                         variants_filter.Parameters.CASE_ID_KEY: "case:concept:name",
                                                         variants_filter.Parameters.ACTIVITY_KEY: "concept:name"})

    def test_32(self):
        from pm4py.algo.filtering.log.attributes import attributes_filter
        log = self.load_running_example_xes()
        activities = attributes_filter.get_attribute_values(log, "concept:name")
        resources = attributes_filter.get_attribute_values(log, "org:resource")

    def test_33(self):
        from pm4py.algo.filtering.pandas.attributes import attributes_filter
        df = self.load_running_example_df()
        activities = attributes_filter.get_attribute_values(df, attribute_key="concept:name")
        resources = attributes_filter.get_attribute_values(df, attribute_key="org:resource")

    def test_34(self):
        from pm4py.algo.filtering.log.attributes import attributes_filter
        log = self.load_receipt_xes()
        tracefilter_log_pos = attributes_filter.apply(log, ["Resource10"],
                                                      parameters={
                                                          attributes_filter.Parameters.ATTRIBUTE_KEY: "org:resource",
                                                          attributes_filter.Parameters.POSITIVE: True})
        tracefilter_log_neg = attributes_filter.apply(log, ["Resource10"],
                                                      parameters={
                                                          attributes_filter.Parameters.ATTRIBUTE_KEY: "org:resource",
                                                          attributes_filter.Parameters.POSITIVE: False})

    def test_35(self):
        from pm4py.algo.filtering.pandas.attributes import attributes_filter
        df = self.load_receipt_df()
        df_traces_pos = attributes_filter.apply(df, ["Resource10"],
                                                parameters={
                                                    attributes_filter.Parameters.CASE_ID_KEY: "case:concept:name",
                                                    attributes_filter.Parameters.ATTRIBUTE_KEY: "org:resource",
                                                    attributes_filter.Parameters.POSITIVE: True})
        df_traces_neg = attributes_filter.apply(df, ["Resource10"],
                                                parameters={
                                                    attributes_filter.Parameters.CASE_ID_KEY: "case:concept:name",
                                                    attributes_filter.Parameters.ATTRIBUTE_KEY: "org:resource",
                                                    attributes_filter.Parameters.POSITIVE: False})

    def test_38(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        log = xes_importer.apply(os.path.join("input_data", "roadtraffic100traces.xes"))

        from pm4py.algo.filtering.log.attributes import attributes_filter
        filtered_log_events = attributes_filter.apply_numeric_events(log, 34, 36,
                                                                     parameters={
                                                                         attributes_filter.Parameters.ATTRIBUTE_KEY: "amount"})

        filtered_log_cases = attributes_filter.apply_numeric(log, 34, 36,
                                                             parameters={
                                                                 attributes_filter.Parameters.ATTRIBUTE_KEY: "amount"})

        filtered_log_cases = attributes_filter.apply_numeric(log, 34, 500,
                                                             parameters={
                                                                 attributes_filter.Parameters.ATTRIBUTE_KEY: "amount",
                                                                 attributes_filter.Parameters.STREAM_FILTER_KEY1: "concept:name",
                                                                 attributes_filter.Parameters.STREAM_FILTER_VALUE1: "Add penalty"})

    def test_39(self):
        import os
        df = pandas_utils.read_csv(os.path.join("input_data", "roadtraffic100traces.csv"))
        df = dataframe_utils.convert_timestamp_columns_in_df(df, timest_format=constants.DEFAULT_TIMESTAMP_PARSE_FORMAT)

        from pm4py.algo.filtering.pandas.attributes import attributes_filter
        filtered_df_events = attributes_filter.apply_numeric_events(df, 34, 36,
                                                                    parameters={
                                                                        attributes_filter.Parameters.CASE_ID_KEY: "case:concept:name",
                                                                        attributes_filter.Parameters.ATTRIBUTE_KEY: "amount"})

        filtered_df_cases = attributes_filter.apply_numeric(df, 34, 36,
                                                            parameters={
                                                                attributes_filter.Parameters.CASE_ID_KEY: "case:concept:name",
                                                                attributes_filter.Parameters.ATTRIBUTE_KEY: "amount"})

        filtered_df_cases = attributes_filter.apply_numeric(df, 34, 500,
                                                            parameters={
                                                                attributes_filter.Parameters.CASE_ID_KEY: "case:concept:name",
                                                                attributes_filter.Parameters.ATTRIBUTE_KEY: "amount",
                                                                attributes_filter.Parameters.STREAM_FILTER_KEY1: "concept:name",
                                                                attributes_filter.Parameters.STREAM_FILTER_VALUE1: "Add penalty"})

    def test_40(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))
        from pm4py.algo.discovery.alpha import algorithm as alpha_miner
        net, initial_marking, final_marking = alpha_miner.apply(log)

    def test_41(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        from pm4py.algo.discovery.inductive import algorithm as inductive_miner

        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))
        process_tree = inductive_miner.apply(log)
        net, initial_marking, final_marking = process_tree_converter.apply(process_tree)

        from pm4py.algo.discovery.inductive import algorithm as inductive_miner
        from pm4py.visualization.process_tree import visualizer as pt_visualizer

        tree = inductive_miner.apply(log)

        gviz = pt_visualizer.apply(tree)

        from pm4py.objects.conversion.process_tree import converter as pt_converter
        net, initial_marking, final_marking = pt_converter.apply(tree, variant=pt_converter.Variants.TO_PETRI_NET)

    def test_42(self):
        from pm4py.objects.log.importer.xes import importer as xes_importer
        import os
        log_path = os.path.join("compressed_input_data", "09_a32f0n00.xes.gz")
        log = xes_importer.apply(log_path)

        from pm4py.algo.discovery.heuristics import algorithm as heuristics_miner
        heu_net = heuristics_miner.apply_heu(log, parameters={
            heuristics_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.99})

        from pm4py.visualization.heuristics_net import visualizer as hn_visualizer
        gviz = hn_visualizer.apply(heu_net)

        from pm4py.algo.discovery.heuristics import algorithm as heuristics_miner
        net, im, fm = heuristics_miner.apply(log, parameters={
            heuristics_miner.Variants.CLASSIC.value.Parameters.DEPENDENCY_THRESH: 0.99})

        from pm4py.visualization.petri_net import visualizer as pn_visualizer
        gviz = pn_visualizer.apply(net, im, fm)

    def test_43(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))

        from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
        dfg = dfg_discovery.apply(log)

        from pm4py.visualization.dfg import visualizer as dfg_visualization
        gviz = dfg_visualization.apply(dfg, log=log, variant=dfg_visualization.Variants.FREQUENCY)

    def test_44(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))

        from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
        from pm4py.visualization.dfg import visualizer as dfg_visualization

        dfg = dfg_discovery.apply(log, variant=dfg_discovery.Variants.PERFORMANCE)
        gviz = dfg_visualization.apply(dfg, log=log, variant=dfg_visualization.Variants.PERFORMANCE)

    def test_45(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))

        from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
        from pm4py.visualization.dfg import visualizer as dfg_visualization

        dfg = dfg_discovery.apply(log, variant=dfg_discovery.Variants.PERFORMANCE)
        parameters = {dfg_visualization.Variants.PERFORMANCE.value.Parameters.FORMAT: "svg"}
        gviz = dfg_visualization.apply(dfg, log=log, variant=dfg_visualization.Variants.PERFORMANCE,
                                       parameters=parameters)

        dfg_visualization.save(gviz, os.path.join("test_output_data", "dfg.svg"))
        os.remove(os.path.join("test_output_data", "dfg.svg"))

    def test_46(self):
        from pm4py.objects.log.importer.xes import importer as xes_importer
        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))

        from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
        dfg = dfg_discovery.apply(log)

        from pm4py.objects.conversion.dfg import converter as dfg_mining
        net, im, fm = dfg_mining.apply(dfg)

    def test_47(self):
        log = self.load_running_example_xes()

        import os
        from pm4py.algo.discovery.inductive import algorithm as inductive_miner
        process_tree = inductive_miner.apply(log)
        net, initial_marking, final_marking = process_tree_converter.apply(process_tree)

        from pm4py.visualization.petri_net import visualizer as pn_visualizer
        parameters = {pn_visualizer.Variants.WO_DECORATION.value.Parameters.FORMAT: "png"}
        gviz = pn_visualizer.apply(net, initial_marking, final_marking, parameters=parameters,
                                   variant=pn_visualizer.Variants.FREQUENCY, log=log)
        pn_visualizer.save(gviz, os.path.join("test_output_data", "inductive_frequency.png"))

        os.remove(os.path.join("test_output_data", "inductive_frequency.png"))

    def test_48(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        from pm4py.algo.discovery.alpha import algorithm as alpha_miner
        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))
        parameters = {alpha_miner.Variants.ALPHA_VERSION_CLASSIC.value.Parameters.ACTIVITY_KEY: "concept:name"}
        net, initial_marking, final_marking = alpha_miner.apply(log, parameters=parameters)

    def test_49(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer

        log = xes_importer.apply(os.path.join("input_data", "receipt.xes"))
        classifiers = log.classifiers

        from pm4py.objects.log.util import insert_classifier
        log, activity_key = insert_classifier.insert_activity_classifier_attribute(log, "Activity classifier")

        from pm4py.algo.discovery.alpha import algorithm as alpha_miner
        parameters = {alpha_miner.Variants.ALPHA_VERSION_CLASSIC.value.Parameters.ACTIVITY_KEY: activity_key}
        net, initial_marking, final_marking = alpha_miner.apply(log, parameters=parameters)

    def test_50(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer

        log = xes_importer.apply(os.path.join("input_data", "receipt.xes"))
        for trace in log:
            for event in trace:
                event["customClassifier"] = event["concept:name"] + event["lifecycle:transition"]

        from pm4py.algo.discovery.alpha import algorithm as alpha_miner
        parameters = {alpha_miner.Variants.ALPHA_VERSION_CLASSIC.value.Parameters.ACTIVITY_KEY: "customClassifier"}
        net, initial_marking, final_marking = alpha_miner.apply(log, parameters=parameters)

    def test_51(self):
        import os
        from pm4py.objects.petri_net.importer import importer as pnml_importer
        net, initial_marking, final_marking = pnml_importer.apply(
            os.path.join("input_data", "running-example.pnml"))

        from pm4py.visualization.petri_net import visualizer as pn_visualizer
        gviz = pn_visualizer.apply(net, initial_marking, final_marking)

        from pm4py.objects.petri_net.exporter import exporter as pnml_exporter
        pnml_exporter.apply(net, initial_marking, "petri.pnml")

        pnml_exporter.apply(net, initial_marking, "petri_final.pnml", final_marking=final_marking)

        os.remove("petri.pnml")
        os.remove("petri_final.pnml")

        from pm4py.objects.petri_net import semantics
        transitions = semantics.enabled_transitions(net, initial_marking)

        places = net.places
        transitions = net.transitions
        arcs = net.arcs

        for place in places:
            stru = "\nPLACE: " + place.name
            for arc in place.in_arcs:
                stru = str(arc.source.name) + " " + str(arc.source.label)

    def test_52(self):
        # creating an empty Petri net
        from pm4py.objects.petri_net.obj import PetriNet, Marking
        net = PetriNet("new_petri_net")

        # creating source, p_1 and sink place
        source = PetriNet.Place("source")
        sink = PetriNet.Place("sink")
        p_1 = PetriNet.Place("p_1")
        # add the places to the Petri Net
        net.places.add(source)
        net.places.add(sink)
        net.places.add(p_1)

        # Create transitions
        t_1 = PetriNet.Transition("name_1", "label_1")
        t_2 = PetriNet.Transition("name_2", "label_2")
        # Add the transitions to the Petri Net
        net.transitions.add(t_1)
        net.transitions.add(t_2)

        # Add arcs
        from pm4py.objects.petri_net.utils import petri_utils
        petri_utils.add_arc_from_to(source, t_1, net)
        petri_utils.add_arc_from_to(t_1, p_1, net)
        petri_utils.add_arc_from_to(p_1, t_2, net)
        petri_utils.add_arc_from_to(t_2, sink, net)

        # Adding tokens
        initial_marking = Marking()
        initial_marking[source] = 1
        final_marking = Marking()
        final_marking[sink] = 1

        from pm4py.objects.petri_net.exporter import exporter as pnml_exporter
        pnml_exporter.apply(net, initial_marking, "createdPetriNet1.pnml", final_marking=final_marking)

        from pm4py.visualization.petri_net import visualizer as pn_visualizer
        gviz = pn_visualizer.apply(net, initial_marking, final_marking)

        from pm4py.visualization.petri_net import visualizer as pn_visualizer
        parameters = {pn_visualizer.Variants.WO_DECORATION.value.Parameters.FORMAT: "svg"}
        gviz = pn_visualizer.apply(net, initial_marking, final_marking, parameters=parameters)

        from pm4py.visualization.petri_net import visualizer as pn_visualizer
        parameters = {pn_visualizer.Variants.WO_DECORATION.value.Parameters.FORMAT: "svg"}
        gviz = pn_visualizer.apply(net, initial_marking, final_marking, parameters=parameters)
        pn_visualizer.save(gviz, "alpha.svg")

        os.remove("createdPetriNet1.pnml")
        os.remove("alpha.svg")

    def test_56(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        from pm4py.algo.discovery.inductive import algorithm as inductive_miner

        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))

        process_tree = inductive_miner.apply(log)
        net, initial_marking, final_marking = process_tree_converter.apply(process_tree)

        from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments
        alignments = alignments.apply_log(log, net, initial_marking, final_marking)

    def test_57(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        from pm4py.algo.discovery.inductive import algorithm as inductive_miner

        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))
        for trace in log:
            for event in trace:
                event["customClassifier"] = event["concept:name"] + event["concept:name"]

        from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments

        # define the activity key in the parameters
        parameters = {inductive_miner.Parameters.ACTIVITY_KEY: "customClassifier",
                      alignments.Variants.VERSION_STATE_EQUATION_A_STAR.value.Parameters.ACTIVITY_KEY: "customClassifier"}

        # calculate process model using the given classifier
        process_tree = inductive_miner.apply(log)
        net, initial_marking, final_marking = process_tree_converter.apply(process_tree)
        alignments = alignments.apply_log(log, net, initial_marking, final_marking, parameters=parameters)

        from pm4py.algo.evaluation.replay_fitness import algorithm as replay_fitness
        log_fitness = replay_fitness.evaluate(alignments, variant=replay_fitness.Variants.ALIGNMENT_BASED)

    def test_58(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        from pm4py.algo.discovery.inductive import algorithm as inductive_miner

        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))

        process_tree = inductive_miner.apply(log)
        net, initial_marking, final_marking = process_tree_converter.apply(process_tree)

        from pm4py.algo.conformance.alignments.petri_net import algorithm as alignments

        model_cost_function = dict()
        sync_cost_function = dict()
        for t in net.transitions:
            # if the label is not None, we have a visible transition
            if t.label is not None:
                # associate cost 1000 to each move-on-model associated to visible transitions
                model_cost_function[t] = 1000
                # associate cost 0 to each move-on-log
                sync_cost_function[t] = 0
            else:
                # associate cost 1 to each move-on-model associated to hidden transitions
                model_cost_function[t] = 1

        parameters = {}
        parameters[
            alignments.Variants.VERSION_STATE_EQUATION_A_STAR.value.Parameters.PARAM_MODEL_COST_FUNCTION] = model_cost_function
        parameters[
            alignments.Variants.VERSION_STATE_EQUATION_A_STAR.value.Parameters.PARAM_SYNC_COST_FUNCTION] = sync_cost_function

        alignments = alignments.apply_log(log, net, initial_marking, final_marking, parameters=parameters)

    def test_59(self):
        from pm4py.algo.simulation.tree_generator import algorithm as tree_gen
        parameters = {}
        tree = tree_gen.apply(parameters=parameters)

        from pm4py.objects.process_tree import semantics
        log = semantics.generate_log(tree, no_traces=100)

        from pm4py.objects.conversion.process_tree import converter as pt_converter
        net, im, fm = pt_converter.apply(tree)

        from pm4py.visualization.process_tree import visualizer as pt_visualizer
        gviz = pt_visualizer.apply(tree, parameters={pt_visualizer.Variants.WO_DECORATION.value.Parameters.FORMAT: "png"})

    def test_60(self):
        if importlib.util.find_spec("sklearn"):
            import os
            from pm4py.objects.log.importer.xes import importer as xes_importer
            log = xes_importer.apply(os.path.join("input_data", "roadtraffic50traces.xes"))

            from pm4py.algo.transformation.log_to_features.variants import trace_based
            str_trace_attributes = []
            str_event_attributes = ["concept:name"]
            num_trace_attributes = []
            num_event_attributes = ["amount"]
            data, feature_names = trace_based.apply(log)
            data, feature_names = trace_based.apply(log, parameters={"str_tr_attr": str_trace_attributes, "str_ev_attr": str_event_attributes, "num_tr_attr": num_trace_attributes, "num_ev_attr": num_event_attributes})

            from pm4py.objects.log.util import get_class_representation
            target, classes = get_class_representation.get_class_representation_by_str_ev_attr_value_value(log,
                                                                                                           "concept:name")

            from pm4py.util import ml_utils
            clf = ml_utils.DecisionTreeClassifier()
            clf.fit(data, target)

            from pm4py.visualization.decisiontree import visualizer as dectree_visualizer
            gviz = dectree_visualizer.apply(clf, feature_names, classes)

    def test_61(self):
        if importlib.util.find_spec("sklearn"):
            import os
            from pm4py.objects.log.importer.xes import importer as xes_importer
            log = xes_importer.apply(os.path.join("input_data", "roadtraffic50traces.xes"))

            from pm4py.algo.transformation.log_to_features.variants import trace_based
            str_trace_attributes = []
            str_event_attributes = ["concept:name"]
            num_trace_attributes = []
            num_event_attributes = ["amount"]
            data, feature_names = trace_based.apply(log)
            data, feature_names = trace_based.apply(log, parameters={"str_tr_attr": str_trace_attributes, "str_ev_attr": str_event_attributes, "num_tr_attr": num_trace_attributes, "num_ev_attr": num_event_attributes})

            from pm4py.objects.log.util import get_class_representation
            target, classes = get_class_representation.get_class_representation_by_trace_duration(log, 2 * 8640000)

            from pm4py.util import ml_utils
            clf = ml_utils.DecisionTreeClassifier()
            clf.fit(data, target)

            from pm4py.visualization.decisiontree import visualizer as dectree_visualizer
            gviz = dectree_visualizer.apply(clf, feature_names, classes)

    def test_62(self):
        from pm4py.objects.log.importer.xes import importer as xes_importer
        xes_importer.Variants.ITERPARSE.value.Parameters.TIMESTAMP_SORT
        xes_importer.Variants.ITERPARSE.value.Parameters.TIMESTAMP_KEY
        xes_importer.Variants.ITERPARSE.value.Parameters.REVERSE_SORT
        xes_importer.Variants.ITERPARSE.value.Parameters.MAX_TRACES

    def test_63(self):
        from pm4py.objects.log.importer.xes import importer as xes_importer
        xes_importer.Variants.LINE_BY_LINE.value.Parameters.TIMESTAMP_SORT
        xes_importer.Variants.LINE_BY_LINE.value.Parameters.TIMESTAMP_KEY
        xes_importer.Variants.LINE_BY_LINE.value.Parameters.REVERSE_SORT
        xes_importer.Variants.LINE_BY_LINE.value.Parameters.MAX_TRACES
        xes_importer.Variants.LINE_BY_LINE.value.Parameters.MAX_BYTES

    def test_64(self):
        from pm4py.objects.conversion.log import converter
        converter.Variants.TO_EVENT_LOG.value.Parameters.STREAM_POST_PROCESSING
        converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ATTRIBUTE_PREFIX
        converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY
        converter.Variants.TO_EVENT_LOG.value.Parameters.DEEP_COPY
        converter.Variants.TO_EVENT_LOG.value.Parameters.CASE_ID_KEY

    def test_65(self):
        from pm4py.objects.conversion.log import converter
        converter.Variants.TO_EVENT_STREAM.value.Parameters.STREAM_POST_PROCESSING
        converter.Variants.TO_EVENT_STREAM.value.Parameters.CASE_ATTRIBUTE_PREFIX
        converter.Variants.TO_EVENT_STREAM.value.Parameters.DEEP_COPY

    def test_66(self):
        from pm4py.objects.conversion.log import converter
        converter.Variants.TO_EVENT_STREAM.value.Parameters.CASE_ATTRIBUTE_PREFIX
        converter.Variants.TO_EVENT_STREAM.value.Parameters.DEEP_COPY

    def test_67(self):
        from pm4py.objects.log.exporter.xes import exporter as xes_exporter
        xes_exporter.Variants.ETREE.value.Parameters.COMPRESS

    def test_tbr_diagn_1(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        log = xes_importer.apply(os.path.join("input_data", "receipt.xes"))

        from pm4py.algo.filtering.log.variants import variants_filter
        filtered_log = variants_filter.filter_log_variants_percentage(log, 0.2)

        from pm4py.algo.discovery.inductive import algorithm as inductive_miner
        process_tree = inductive_miner.apply(log)
        net, initial_marking, final_marking = process_tree_converter.apply(process_tree)

        from pm4py.algo.conformance.tokenreplay import algorithm as token_based_replay
        parameters_tbr = {token_based_replay.Variants.TOKEN_REPLAY.value.Parameters.DISABLE_VARIANTS: True,
                          token_based_replay.Variants.TOKEN_REPLAY.value.Parameters.ENABLE_PLTR_FITNESS: True}
        replayed_traces, place_fitness, trans_fitness, unwanted_activities = token_based_replay.apply(log, net,
                                                                                                      initial_marking,
                                                                                                      final_marking,
                                                                                                      parameters=parameters_tbr)

        from pm4py.algo.conformance.tokenreplay.diagnostics import duration_diagnostics
        trans_diagnostics = duration_diagnostics.diagnose_from_trans_fitness(log, trans_fitness)
        for trans in trans_diagnostics:
            #print(trans, trans_diagnostics[trans])
            pass

        from pm4py.algo.conformance.tokenreplay.diagnostics import duration_diagnostics
        act_diagnostics = duration_diagnostics.diagnose_from_notexisting_activities(log, unwanted_activities)
        for act in act_diagnostics:
            #print(act, act_diagnostics[act])
            pass

    def test_tbr_diagn_2(self):
        if importlib.util.find_spec("sklearn"):
            import os
            from pm4py.objects.log.importer.xes import importer as xes_importer
            log = xes_importer.apply(os.path.join("input_data", "receipt.xes"))

            from pm4py.algo.filtering.log.variants import variants_filter
            filtered_log = variants_filter.filter_log_variants_percentage(log, 0.2)

            from pm4py.algo.discovery.inductive import algorithm as inductive_miner
            process_tree = inductive_miner.apply(log)
            net, initial_marking, final_marking = process_tree_converter.apply(process_tree)

            # build decision trees
            string_attributes = ["org:group"]
            numeric_attributes = []
            parameters = {"string_attributes": string_attributes, "numeric_attributes": numeric_attributes}

            from pm4py.algo.conformance.tokenreplay import algorithm as token_based_replay
            parameters_tbr = {token_based_replay.Variants.TOKEN_REPLAY.value.Parameters.DISABLE_VARIANTS: True,
                              token_based_replay.Variants.TOKEN_REPLAY.value.Parameters.ENABLE_PLTR_FITNESS: True}
            replayed_traces, place_fitness, trans_fitness, unwanted_activities = token_based_replay.apply(log, net,
                                                                                                          initial_marking,
                                                                                                          final_marking,
                                                                                                          parameters=parameters_tbr)

            from pm4py.algo.conformance.tokenreplay.diagnostics import root_cause_analysis
            trans_root_cause = root_cause_analysis.diagnose_from_trans_fitness(log, trans_fitness, parameters=parameters)


            from pm4py.visualization.decisiontree import visualizer as dt_vis
            for trans in trans_root_cause:
                clf = trans_root_cause[trans]["clf"]
                feature_names = trans_root_cause[trans]["feature_names"]
                classes = trans_root_cause[trans]["classes"]

                # visualization could be called
                gviz = dt_vis.apply(clf, feature_names, classes)
                break

            from pm4py.algo.conformance.tokenreplay.diagnostics import root_cause_analysis
            act_root_cause = root_cause_analysis.diagnose_from_notexisting_activities(log, unwanted_activities,
                                                                                      parameters=parameters)

            from pm4py.visualization.decisiontree import visualizer as dt_vis
            for act in act_root_cause:
                clf = act_root_cause[act]["clf"]
                feature_names = act_root_cause[act]["feature_names"]
                classes = act_root_cause[act]["classes"]
                # visualization could be called
                gviz = dt_vis.apply(clf, feature_names, classes)
                break

    def test_max_decomp(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        from pm4py.algo.discovery.alpha import algorithm as alpha_miner

        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))
        net, im, fm = alpha_miner.apply(log)

        from pm4py.objects.petri_net.utils.decomposition import decompose

        list_nets = decompose(net, im, fm)

        from pm4py.visualization.petri_net import visualizer
        gviz = []
        for index, model in enumerate(list_nets):
            subnet, s_im, s_fm = model

            gviz.append(visualizer.apply(subnet, s_im, s_fm, parameters={visualizer.Variants.WO_DECORATION.value.Parameters.FORMAT: "png"}))
            break

    def test_reach_graph(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        from pm4py.algo.discovery.alpha import algorithm as alpha_miner

        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))
        net, im, fm = alpha_miner.apply(log)

        from pm4py.objects.petri_net.utils import reachability_graph

        ts = reachability_graph.construct_reachability_graph(net, im)

        from pm4py.visualization.transition_system import visualizer as ts_visualizer

        gviz = ts_visualizer.apply(ts, parameters={ts_visualizer.Variants.VIEW_BASED.value.Parameters.FORMAT: "svg"})

    def test_decomp(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        from pm4py.algo.discovery.alpha import algorithm as alpha_miner

        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))
        net, im, fm = alpha_miner.apply(log)

        from pm4py.algo.conformance.alignments.decomposed import algorithm as decomp_alignments

        conf = decomp_alignments.apply(log, net, im, fm, parameters={
            decomp_alignments.Variants.RECOMPOS_MAXIMAL.value.Parameters.PARAM_THRESHOLD_BORDER_AGREEMENT: 2})

        from pm4py.algo.evaluation.replay_fitness import algorithm as rp_fitness_evaluator

        fitness = rp_fitness_evaluator.evaluate(conf, variant=rp_fitness_evaluator.Variants.ALIGNMENT_BASED)

    def test_footprints(self):
        from pm4py.objects.log.importer.xes import importer as xes_importer
        import os
        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))

        from pm4py.algo.discovery.inductive import algorithm as inductive_miner
        process_tree = inductive_miner.apply(log)
        net, im, fm = process_tree_converter.apply(process_tree)

        from pm4py.algo.discovery.footprints import algorithm as footprints_discovery

        fp_log = footprints_discovery.apply(log, variant=footprints_discovery.Variants.ENTIRE_EVENT_LOG)

        from pm4py.algo.discovery.footprints import algorithm as footprints_discovery

        fp_trace_by_trace = footprints_discovery.apply(log, variant=footprints_discovery.Variants.TRACE_BY_TRACE)

        fp_net = footprints_discovery.apply(net, im, fm)

        from pm4py.visualization.footprints import visualizer as fp_visualizer

        gviz = fp_visualizer.apply(fp_net, parameters={fp_visualizer.Variants.SINGLE.value.Parameters.FORMAT: "svg"})

        from pm4py.visualization.footprints import visualizer as fp_visualizer

        gviz = fp_visualizer.apply(fp_log, fp_net,
                                   parameters={fp_visualizer.Variants.COMPARISON.value.Parameters.FORMAT: "svg"})

        from pm4py.objects.log.importer.xes import importer as xes_importer
        import os
        from copy import deepcopy
        from pm4py.algo.filtering.log.variants import variants_filter

        log = xes_importer.apply(os.path.join("input_data", "receipt.xes"))
        filtered_log = variants_filter.filter_log_variants_percentage(log, 0.2)

        from pm4py.algo.discovery.inductive import algorithm as inductive_miner
        process_tree = inductive_miner.apply(log)
        net, im, fm = process_tree_converter.apply(process_tree)

        from pm4py.algo.conformance.footprints import algorithm as footprints_conformance

        conf_fp = footprints_conformance.apply(fp_trace_by_trace, fp_net)

    def test_log_skeleton(self):
        from pm4py.objects.log.importer.xes import importer as xes_importer
        import os
        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))

        from pm4py.algo.discovery.log_skeleton import algorithm as lsk_discovery
        skeleton = lsk_discovery.apply(log, parameters={
            lsk_discovery.Variants.CLASSIC.value.Parameters.NOISE_THRESHOLD: 0.0})

        from pm4py.objects.log.importer.xes import importer as xes_importer
        import os
        log = xes_importer.apply(os.path.join("input_data", "receipt.xes"))
        from copy import deepcopy
        from pm4py.algo.filtering.log.variants import variants_filter
        filtered_log = variants_filter.filter_log_variants_percentage(log, 0.2)

        from pm4py.algo.conformance.log_skeleton import algorithm as lsk_conformance
        conf_result = lsk_conformance.apply(log, skeleton)

        from pm4py.algo.discovery.log_skeleton import algorithm as lsk_discovery
        skeleton = lsk_discovery.apply(log, parameters={
            lsk_discovery.Variants.CLASSIC.value.Parameters.NOISE_THRESHOLD: 0.03})

        from pm4py.algo.conformance.log_skeleton import algorithm as lsk_conformance
        conf_result = lsk_conformance.apply(log, skeleton)

    def test_throughput_time(self):
        from pm4py.objects.log.importer.xes import importer as xes_importer
        import os
        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))

        from pm4py.statistics.traces.generic.log import case_statistics
        all_case_durations = case_statistics.get_all_case_durations(log, parameters={
            case_statistics.Parameters.TIMESTAMP_KEY: "time:timestamp"})

        from pm4py.statistics.traces.generic.log import case_statistics
        median_case_duration = case_statistics.get_median_case_duration(log, parameters={
            case_statistics.Parameters.TIMESTAMP_KEY: "time:timestamp"
        })

    def test_case_arrival(self):
        from pm4py.objects.log.importer.xes import importer as xes_importer
        import os
        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))

        from pm4py.statistics.traces.generic.log import case_arrival
        case_arrival_ratio = case_arrival.get_case_arrival_avg(log, parameters={
            case_arrival.Parameters.TIMESTAMP_KEY: "time:timestamp"})

        from pm4py.statistics.traces.generic.log import case_arrival
        case_dispersion_ratio = case_arrival.get_case_dispersion_avg(log, parameters={
            case_arrival.Parameters.TIMESTAMP_KEY: "time:timestamp"})

    def test_ps(self):
        from pm4py.objects.log.importer.xes import importer as xes_importer
        import os
        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))

        from pm4py.algo.discovery.performance_spectrum import algorithm as performance_spectrum
        ps = performance_spectrum.apply(log, ["register request", "decide"],
                                        parameters={performance_spectrum.Parameters.ACTIVITY_KEY: "concept:name",
                                                    performance_spectrum.Parameters.TIMESTAMP_KEY: "time:timestamp"})

    def test_business_hours(self):
        from pm4py.util.business_hours import BusinessHours
        from datetime import datetime
        from pm4py.util.dt_parsing.variants import strpfromiso
        from pm4py.util import constants

        st = strpfromiso.fix_naivety(datetime.fromtimestamp(100000000))
        et = strpfromiso.fix_naivety(datetime.fromtimestamp(200000000))
        bh_object = BusinessHours(st, et)
        worked_time = bh_object.get_seconds()

        bh_object = BusinessHours(st, et, business_hour_slots=constants.DEFAULT_BUSINESS_HOUR_SLOTS)
        worked_time = bh_object.get_seconds()

    def test_cycle_waiting_time(self):
        from pm4py.objects.log.importer.xes import importer as xes_importer
        import os
        log = xes_importer.apply(os.path.join("input_data", "receipt.xes"))

        from pm4py.objects.log.util import interval_lifecycle
        enriched_log = interval_lifecycle.assign_lead_cycle_time(log)

    def test_distr_case_duration(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        log_path = os.path.join("input_data", "receipt.xes")
        log = xes_importer.apply(log_path)

        from pm4py.util import constants
        from pm4py.statistics.traces.generic.log import case_statistics
        x, y = case_statistics.get_kde_caseduration(log, parameters={
            constants.PARAMETER_CONSTANT_TIMESTAMP_KEY: "time:timestamp"})

        if importlib.util.find_spec("matplotlib"):
            from pm4py.visualization.graphs import visualizer as graphs_visualizer

            gviz = graphs_visualizer.apply_plot(x, y, variant=graphs_visualizer.Variants.CASES)
            gviz = graphs_visualizer.apply_semilogx(x, y, variant=graphs_visualizer.Variants.CASES)

    def test_distr_num_attribute(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer

        log_path = os.path.join("input_data", "roadtraffic100traces.xes")
        log = xes_importer.apply(log_path)

        from pm4py.algo.filtering.log.attributes import attributes_filter

        x, y = attributes_filter.get_kde_numeric_attribute(log, "amount")

        if importlib.util.find_spec("matplotlib"):
            from pm4py.visualization.graphs import visualizer as graphs_visualizer

            gviz = graphs_visualizer.apply_plot(x, y, variant=graphs_visualizer.Variants.ATTRIBUTES)

            from pm4py.visualization.graphs import visualizer as graphs_visualizer

            gviz = graphs_visualizer.apply_semilogx(x, y, variant=graphs_visualizer.Variants.ATTRIBUTES)

    def test_evaluation(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        from pm4py.algo.discovery.alpha import algorithm as alpha_miner

        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))
        net, im, fm = alpha_miner.apply(log)

        from pm4py.algo.evaluation.replay_fitness import algorithm as replay_fitness_evaluator
        fitness = replay_fitness_evaluator.apply(log, net, im, fm,
                                                 variant=replay_fitness_evaluator.Variants.TOKEN_BASED)

        from pm4py.algo.evaluation.replay_fitness import algorithm as replay_fitness_evaluator
        fitness = replay_fitness_evaluator.apply(log, net, im, fm,
                                                 variant=replay_fitness_evaluator.Variants.ALIGNMENT_BASED)

        from pm4py.algo.evaluation.precision import algorithm as precision_evaluator
        prec = precision_evaluator.apply(log, net, im, fm, variant=precision_evaluator.Variants.ETCONFORMANCE_TOKEN)

        from pm4py.algo.evaluation.precision import algorithm as precision_evaluator
        prec = precision_evaluator.apply(log, net, im, fm, variant=precision_evaluator.Variants.ALIGN_ETCONFORMANCE)

        from pm4py.algo.evaluation.generalization import algorithm as generalization_evaluator
        gen = generalization_evaluator.apply(log, net, im, fm)

        from pm4py.algo.evaluation.simplicity import algorithm as simplicity_evaluator
        simp = simplicity_evaluator.apply(net)

    def test_sna(self):
        if importlib.util.find_spec("pyvis"):
            import os
            from pm4py.objects.log.importer.xes import importer as xes_importer

            log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))

            from pm4py.algo.organizational_mining.sna import algorithm as sna
            hw_values = sna.apply(log, variant=sna.Variants.HANDOVER_LOG)

            from pm4py.visualization.sna import visualizer as sna_visualizer
            gviz_hw_py = sna_visualizer.apply(hw_values, variant=sna_visualizer.Variants.PYVIS)

            from pm4py.algo.organizational_mining.sna import algorithm as sna
            sub_values = sna.apply(log, variant=sna.Variants.SUBCONTRACTING_LOG)

            from pm4py.visualization.sna import visualizer as sna_visualizer
            gviz_sub_py = sna_visualizer.apply(sub_values, variant=sna_visualizer.Variants.PYVIS)

            from pm4py.algo.organizational_mining.sna import algorithm as sna
            wt_values = sna.apply(log, variant=sna.Variants.WORKING_TOGETHER_LOG)

            from pm4py.visualization.sna import visualizer as sna_visualizer
            gviz_wt_py = sna_visualizer.apply(wt_values, variant=sna_visualizer.Variants.PYVIS)

            from pm4py.algo.organizational_mining.sna import algorithm as sna
            ja_values = sna.apply(log, variant=sna.Variants.JOINTACTIVITIES_LOG)

            from pm4py.visualization.sna import visualizer as sna_visualizer
            gviz_ja_py = sna_visualizer.apply(ja_values, variant=sna_visualizer.Variants.PYVIS)

            from pm4py.algo.organizational_mining.roles import algorithm as roles_discovery
            roles = roles_discovery.apply(log)

    def test_playout(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        from pm4py.algo.discovery.alpha import algorithm as alpha_miner

        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))
        net, im, fm = alpha_miner.apply(log)

        from pm4py.algo.simulation.playout.petri_net import algorithm

        simulated_log = algorithm.apply(net, im, variant=algorithm.Variants.BASIC_PLAYOUT,
                                        parameters={algorithm.Variants.BASIC_PLAYOUT.value.Parameters.NO_TRACES: 50})

        from pm4py.algo.simulation.playout.petri_net import algorithm

        simulated_log = algorithm.apply(net, im, variant=algorithm.Variants.EXTENSIVE,
                                        parameters={algorithm.Variants.EXTENSIVE.value.Parameters.MAX_TRACE_LENGTH: 7})

    def test_ctmc(self):
        import os
        from pm4py.objects.log.importer.xes import importer as xes_importer
        log = xes_importer.apply(os.path.join("input_data", "running-example.xes"))
        from pm4py.algo.discovery.dfg import algorithm as dfg_discovery
        dfg_perf = dfg_discovery.apply(log, variant=dfg_discovery.Variants.PERFORMANCE)
        from pm4py.statistics.start_activities.log import get as start_activities
        from pm4py.statistics.end_activities.log import get as end_activities
        sa = start_activities.get_start_activities(log)
        ea = end_activities.get_end_activities(log)

        from pm4py.algo.filtering.log.variants import variants_filter
        log = variants_filter.filter_log_variants_percentage(log, 0.2)

        from pm4py.objects.stochastic_petri import ctmc
        reach_graph, tang_reach_graph, stochastic_map, q_matrix = ctmc.get_tangible_reachability_and_q_matrix_from_dfg_performance(
            dfg_perf, parameters={"start_activities": sa, "end_activities": ea})

        # pick the source state
        state = [x for x in tang_reach_graph.states if x.name == "source1"][0]
        # analyse the distribution over the states of the system starting from the source after 172800.0 seconds (2 days)
        transient_result = ctmc.transient_analysis_from_tangible_q_matrix_and_single_state(tang_reach_graph, q_matrix,
                                                                                           state,
                                                                                           172800.0)


if __name__ == "__main__":
    unittest.main()
