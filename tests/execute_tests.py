import argparse
import inspect
import os
import time
import sys
import unittest
import importlib.util

from config import test_config

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

EXECUTE_TESTS = True

import pm4py
import numpy
import pandas
import importlib.util
import networkx

pm4py.util.constants.SHOW_PROGRESS_BAR = False
pm4py.util.constants.SHOW_EVENT_LOG_DEPRECATION = False
pm4py.util.constants.SHOW_INTERNAL_WARNINGS = False
# pm4py.util.constants.DEFAULT_TIMESTAMP_PARSE_FORMAT = None

enabled_tests = [
    "SimplifiedInterfaceTest", "SimplifiedInterface2Test", "DocTests", "RoleDetectionTest",
    "PassedTimeTest", "Pm4pyImportPackageTest", "XesImportExportTest", "CsvImportExportTest",
    "OtherPartsTests", "AlphaMinerTest", "InductiveMinerTest", "InductiveMinerTreeTest",
    "AlignmentTest", "DfgTests", "SnaTests", "PetriImportExportTest", "BPMNTests", "ETCTest",
    "DiagnDfConfChecking", "ProcessModelEvaluationTests", "DecisionTreeTest", "GraphsForming",
    "HeuMinerTest", "MainFactoriesTest", "AlgorithmTest", "LogFilteringTest",
    "DataframePrefilteringTest", "StatisticsLogTest", "StatisticsDfTest", "TransitionSystemTest",
    "ImpExpFromString", "WoflanTest", "OcelFilteringTest", "OcelDiscoveryTest", "LlmTest",
    "OcCausalNetSemanticsTest", "OcCausalNetSimulationTest", "OcCausalNetTest",
    "OcpnSemanticsTest", "OcpnSimulationTest", "OcpnTest", "LocalProcessModelsTest",
    "AdditionalCoverageTest", "ApproxAlignmentTest", "TestGeneticMiner",
    "Ocel2CsvTest", "Ocel2GzipTest", "OcelOlapTest", "SimulationTest",
    "TraceEncodingsTest", "SplitMinerInternalsTest", "ExtendedCoverageTest",
    "CoverageRegressionTest", "ModelUtilitiesCoverageTest",
    "GraphAnalysisCoverageTest", "LogAlgorithmsCoverageTest",
    "PrivacyCoverageTest", "PetriNetExtraCoverageTest", "OcelDeepCoverageTest",
    "PowlDiscoveryCoverageTest", "ConnectorsCoverageTest", "LlmCoverageTest",
    "ClusteringDistanceCoverageTest", "VisualPerformanceCoverageTest",
    "XesDeepCoverageTest", "BpmnDeepCoverageTest", "FacadeUtilsCoverageTest",
    "ProcessTreePetriDeepCoverageTest", "ConformanceDecisionDeepCoverageTest",
    "MiscSubsystemsCoverageTest", "VisualizationFacadeDeepCoverageTest",
    "SerializationLogUtilsCoverageTest", "PetriStochasticSerializationCoverageTest",
    "PowlTreeGenerationDeepCoverageTest",
    "RemainingAlgorithmsCoverageTest", "IoFilteringEdgeCoverageTest",
    "FinalBufferCoverageTest", "LpSolverTest", "BusinessHoursTest"
]

if importlib.util.find_spec("polars"):
    enabled_tests.append("TestPolarsCompatibility")
    enabled_tests.append("PolarsAnalyticsDeepCoverageTest")
    enabled_tests.append("TestPolarsFilteringSimplified")
    enabled_tests.append("TestPolarsFiltering")
    enabled_tests.append("TestPolarsStatistics")
    enabled_tests.append("TestPolarsStatisticsSimplified")
    enabled_tests.append("TestPolarsProcessDiscovery")
    enabled_tests.append("TestPolarsProcessConformance")

loader = unittest.TestLoader()
suite = unittest.TestSuite()

if "BusinessHoursTest" in enabled_tests:
    from tests.business_hours_test import (
        BusinessHoursTest, ScheduledBusinessHoursTest,
    )
    suite.addTests(loader.loadTestsFromTestCase(BusinessHoursTest))
    suite.addTests(loader.loadTestsFromTestCase(ScheduledBusinessHoursTest))

# 'failed' is used to count how many tests or imports fail.
failed = 0

# Check for some required packages
if not importlib.util.find_spec("graphviz"):
    print("important! install 'grapviz' from pip")
    failed += 1

if not importlib.util.find_spec("lxml"):
    print("important! install 'lxml' from pip")
    failed += 1

# Now try to import and add each test class to the suite
if "SimplifiedInterfaceTest" in enabled_tests:
    try:
        from tests.simplified_interface import SimplifiedInterfaceTest
        suite.addTests(loader.loadTestsFromTestCase(SimplifiedInterfaceTest))
    except:
        print("SimplifiedInterfaceTest import failed!")
        failed += 1

if "SimplifiedInterface2Test" in enabled_tests:
    try:
        from tests.simplified_interface_2 import SimplifiedInterface2Test
        suite.addTests(loader.loadTestsFromTestCase(SimplifiedInterface2Test))
    except:
        print("SimplifiedInterface2Test import failed!")
        failed += 1

if "DocTests" in enabled_tests:
    try:
        from tests.doc_tests import DocTests
        suite.addTests(loader.loadTestsFromTestCase(DocTests))
    except:
        print("DocTests import failed!")
        failed += 1

if "RoleDetectionTest" in enabled_tests:
    try:
        from tests.role_detection import RoleDetectionTest
        suite.addTests(loader.loadTestsFromTestCase(RoleDetectionTest))
    except:
        print("RoleDetectionTest import failed!")
        failed += 1

if "PassedTimeTest" in enabled_tests:
    try:
        from tests.passed_time import PassedTimeTest
        suite.addTests(loader.loadTestsFromTestCase(PassedTimeTest))
    except:
        print("PassedTimeTest import failed!")
        failed += 1

if "Pm4pyImportPackageTest" in enabled_tests:
    try:
        from tests.imp_everything import Pm4pyImportPackageTest
        suite.addTests(loader.loadTestsFromTestCase(Pm4pyImportPackageTest))
    except:
        print("Pm4pyImportPackageTest import failed!")
        failed += 1

if "XesImportExportTest" in enabled_tests:
    try:
        from tests.xes_impexp_test import XesImportExportTest
        suite.addTests(loader.loadTestsFromTestCase(XesImportExportTest))
    except:
        print("XesImportExportTest import failed!")
        failed += 1

if "CsvImportExportTest" in enabled_tests:
    try:
        from tests.csv_impexp_test import CsvImportExportTest
        suite.addTests(loader.loadTestsFromTestCase(CsvImportExportTest))
    except:
        print("CsvImportExportTest import failed!")
        failed += 1

if "OtherPartsTests" in enabled_tests:
    try:
        from tests.other_tests import OtherPartsTests
        suite.addTests(loader.loadTestsFromTestCase(OtherPartsTests))
    except:
        print("OtherPartsTests import failed!")
        failed += 1

if "AlphaMinerTest" in enabled_tests:
    try:
        from tests.alpha_test import AlphaMinerTest
        suite.addTests(loader.loadTestsFromTestCase(AlphaMinerTest))
    except:
        print("AlphaMinerTest import failed!")
        failed += 1

if "InductiveMinerTest" in enabled_tests:
    try:
        from tests.inductive_test import InductiveMinerTest
        suite.addTests(loader.loadTestsFromTestCase(InductiveMinerTest))
    except:
        print("InductiveMinerTest import failed!")
        failed += 1

if "InductiveMinerTreeTest" in enabled_tests:
    try:
        from tests.inductive_tree_test import InductiveMinerTreeTest
        suite.addTests(loader.loadTestsFromTestCase(InductiveMinerTreeTest))
    except:
        print("InductiveMinerTreeTest import failed!")
        failed += 1

if "LocalProcessModelsTest" in enabled_tests:
    try:
        from tests.local_process_models_test import LocalProcessModelsTest
        suite.addTests(loader.loadTestsFromTestCase(LocalProcessModelsTest))
    except:
        print("LocalProcessModelsTest import failed!")
        failed += 1

if "AlignmentTest" in enabled_tests:
    try:
        from tests.alignment_test import AlignmentTest
        suite.addTests(loader.loadTestsFromTestCase(AlignmentTest))
    except:
        print("AlignmentTest import failed!")
        failed += 1

if "DfgTests" in enabled_tests:
    try:
        from tests.dfg_tests import DfgTests
        suite.addTests(loader.loadTestsFromTestCase(DfgTests))
    except:
        print("DfgTests import failed!")
        failed += 1

if "SnaTests" in enabled_tests:
    try:
        from tests.sna_test import SnaTests
        suite.addTests(loader.loadTestsFromTestCase(SnaTests))
    except:
        print("SnaTests import failed!")
        failed += 1

if "PetriImportExportTest" in enabled_tests:
    try:
        from tests.petri_imp_exp_test import PetriImportExportTest
        suite.addTests(loader.loadTestsFromTestCase(PetriImportExportTest))
    except:
        print("PetriImportExportTest import failed!")
        failed += 1

if "BPMNTests" in enabled_tests:
    try:
        from tests.bpmn_tests import BPMNTests
        suite.addTests(loader.loadTestsFromTestCase(BPMNTests))
    except:
        print("BPMNTests import failed!")
        failed += 1

if "ETCTest" in enabled_tests:
    try:
        from tests.etc_tests import ETCTest
        suite.addTests(loader.loadTestsFromTestCase(ETCTest))
    except:
        print("ETCTest import failed!")
        failed += 1

if "DiagnDfConfChecking" in enabled_tests:
    try:
        from tests.diagn_df_conf_checking import DiagnDfConfChecking
        suite.addTests(loader.loadTestsFromTestCase(DiagnDfConfChecking))
    except:
        print("DiagnDfConfChecking import failed!")
        failed += 1

if "ProcessModelEvaluationTests" in enabled_tests:
    try:
        from tests.evaluation_tests import ProcessModelEvaluationTests
        suite.addTests(loader.loadTestsFromTestCase(ProcessModelEvaluationTests))
    except:
        print("ProcessModelEvaluationTests import failed!")
        failed += 1

if "DecisionTreeTest" in enabled_tests:
    try:
        from tests.dec_tree_test import DecisionTreeTest
        suite.addTests(loader.loadTestsFromTestCase(DecisionTreeTest))
    except:
        print("DecisionTreeTest import failed!")
        failed += 1

if "GraphsForming" in enabled_tests:
    try:
        from tests.graphs_forming import GraphsForming
        suite.addTests(loader.loadTestsFromTestCase(GraphsForming))
    except:
        print("GraphsForming import failed!")
        failed += 1

if "HeuMinerTest" in enabled_tests:
    try:
        from tests.heuminer_test import HeuMinerTest
        suite.addTests(loader.loadTestsFromTestCase(HeuMinerTest))
    except:
        print("HeuMinerTest import failed!")
        failed += 1

if "MainFactoriesTest" in enabled_tests:
    try:
        from tests.main_fac_test import MainFactoriesTest
        suite.addTests(loader.loadTestsFromTestCase(MainFactoriesTest))
    except:
        print("MainFactoriesTest import failed!")
        failed += 1

if "AlgorithmTest" in enabled_tests:
    try:
        from tests.algorithm_test import AlgorithmTest
        suite.addTests(loader.loadTestsFromTestCase(AlgorithmTest))
    except:
        print("AlgorithmTest import failed!")
        failed += 1

if "LogFilteringTest" in enabled_tests:
    try:
        from tests.filtering_log_test import LogFilteringTest
        suite.addTests(loader.loadTestsFromTestCase(LogFilteringTest))
    except:
        print("LogFilteringTest import failed!")
        failed += 1

if "DataframePrefilteringTest" in enabled_tests:
    try:
        from tests.filtering_pandas_test import DataframePrefilteringTest
        suite.addTests(loader.loadTestsFromTestCase(DataframePrefilteringTest))
    except:
        print("DataframePrefilteringTest import failed!")
        failed += 1

if "StatisticsLogTest" in enabled_tests:
    try:
        from tests.statistics_log_test import StatisticsLogTest
        suite.addTests(loader.loadTestsFromTestCase(StatisticsLogTest))
    except:
        print("StatisticsLogTest import failed!")
        failed += 1

if "StatisticsDfTest" in enabled_tests:
    try:
        from tests.statistics_df_test import StatisticsDfTest
        suite.addTests(loader.loadTestsFromTestCase(StatisticsDfTest))
    except:
        print("StatisticsDfTest import failed!")
        failed += 1

if "TransitionSystemTest" in enabled_tests:
    try:
        from tests.trans_syst_tests import TransitionSystemTest
        suite.addTests(loader.loadTestsFromTestCase(TransitionSystemTest))
    except:
        print("TransitionSystemTest import failed!")
        failed += 1

if "ImpExpFromString" in enabled_tests:
    try:
        from tests.imp_exp_from_string import ImpExpFromString
        suite.addTests(loader.loadTestsFromTestCase(ImpExpFromString))
    except:
        print("ImpExpFromString import failed!")
        failed += 1

if "WoflanTest" in enabled_tests:
    try:
        from tests.woflan_tests import WoflanTest
        suite.addTests(loader.loadTestsFromTestCase(WoflanTest))
    except:
        print("WoflanTest import failed!")
        failed += 1

if "OcelFilteringTest" in enabled_tests:
    try:
        from tests.ocel_filtering_test import OcelFilteringTest
        suite.addTests(loader.loadTestsFromTestCase(OcelFilteringTest))
    except:
        print("OcelFilteringTest import failed!")
        failed += 1

if "OcelDiscoveryTest" in enabled_tests:
    try:
        from tests.ocel_discovery_test import OcelDiscoveryTest
        suite.addTests(loader.loadTestsFromTestCase(OcelDiscoveryTest))
    except:
        print("OcelDiscoveryTest import failed!")
        failed += 1

if "LlmTest" in enabled_tests:
    try:
        from tests.llm_test import LlmTest
        suite.addTests(loader.loadTestsFromTestCase(LlmTest))
    except:
        print("LlmTest import failed!")
        failed += 1

if "OcCausalNetSemanticsTest" in enabled_tests:
    try:
        from tests.oc_causal_net_semantics_test import OCCausalNetSemanticsTest
        suite.addTests(loader.loadTestsFromTestCase(OCCausalNetSemanticsTest))
    except:
        print("OcCausalNetSemanticsTest import failed!")
        failed += 1

if "OcCausalNetSimulationTest" in enabled_tests:
    try:
        from tests.oc_causal_net_simulation_test import OCCausalNetSimulationTest
        suite.addTests(loader.loadTestsFromTestCase(OCCausalNetSimulationTest))
    except:
        print("OcCausalNetSimulationTest import failed!")
        failed += 1

if "OcCausalNetTest" in enabled_tests:
    try:
        from tests.oc_causal_net_test import OCCausalNetTest
        suite.addTests(loader.loadTestsFromTestCase(OCCausalNetTest))
    except:
        print("OcCausalNetTest import failed!")
        failed += 1

if "OcpnSemanticsTest" in enabled_tests:
    try:
        from tests.ocpn_semantics_test import OCPN_Semantics_Test
        suite.addTests(loader.loadTestsFromTestCase(OCPN_Semantics_Test))
    except:
        print("OcpnSemanticsTest import failed!")
        failed += 1

if "OcpnSimulationTest" in enabled_tests:
    try:
        from tests.ocpn_simulation_test import OCPNSimulationTest
        suite.addTests(loader.loadTestsFromTestCase(OCPNSimulationTest))
    except:
        print("OcpnSimulationTest import failed!")
        failed += 1

if "OcpnTest" in enabled_tests:
    try:
        from tests.ocpn_test import OCPN_Test
        suite.addTests(loader.loadTestsFromTestCase(OCPN_Test))
    except:
        print("OCPN_Test import failed!")
        failed += 1

if "TestPolarsCompatibility" in enabled_tests:
    try:
        from tests.polars_compatibility_test import TestPolarsCompatibility
        suite.addTests(loader.loadTestsFromTestCase(TestPolarsCompatibility))
    except:
        print("TestPolarsCompatibility import failed!")
        failed += 1

if "TestPolarsFilteringSimplified" in enabled_tests:
    try:
        from tests.polars_filters_simp_interface import TestPolarsFilteringSimplified
        suite.addTests(loader.loadTestsFromTestCase(TestPolarsFilteringSimplified))
    except:
        print("TestPolarsFilteringSimplified import failed!")
        failed += 1

if "TestPolarsFiltering" in enabled_tests:
    try:
        from tests.polars_filters_test import TestPolarsFiltering
        suite.addTests(loader.loadTestsFromTestCase(TestPolarsFiltering))
    except:
        print("TestPolarsFiltering import failed!")
        failed += 1

if "TestPolarsStatistics" in enabled_tests:
    try:
        from tests.polars_statistics_get import TestPolarsStatistics
        suite.addTests(loader.loadTestsFromTestCase(TestPolarsStatistics))
    except:
        print("TestPolarsStatistics import failed!")
        failed += 1

if "TestPolarsStatisticsSimplified" in enabled_tests:
    try:
        from tests.polars_statistics_simp_interface import TestPolarsStatisticsSimplified
        suite.addTests(loader.loadTestsFromTestCase(TestPolarsStatisticsSimplified))
    except:
        print("TestPolarsStatisticsSimplified import failed!")
        failed += 1

if "TestPolarsProcessDiscovery" in enabled_tests:
    try:
        from tests.polars_process_discovery_test import TestPolarsProcessDiscovery
        suite.addTests(loader.loadTestsFromTestCase(TestPolarsProcessDiscovery))
    except:
        print("TestPolarsProcessDiscovery import failed!")
        failed += 1

if "TestPolarsProcessConformance" in enabled_tests:
    try:
        from tests.polars_cc_test import TestPolarsProcessConformance
        suite.addTests(loader.loadTestsFromTestCase(TestPolarsProcessConformance))
    except:
        print("TestPolarsProcessConformance import failed!")
        failed += 1

if "AdditionalCoverageTest" in enabled_tests:
    try:
        from tests.additional_coverage_test import AdditionalCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(AdditionalCoverageTest))
    except Exception:
        print("AdditionalCoverageTest import failed!")
        failed += 1

if "LpSolverTest" in enabled_tests:
    try:
        from tests.lp_solver_test import LpSolverTest
        suite.addTests(loader.loadTestsFromTestCase(LpSolverTest))
    except Exception:
        print("LpSolverTest import failed!")
        failed += 1

if "ApproxAlignmentTest" in enabled_tests:
    try:
        from tests.approx_alignment_test import ApproxAlignmentTest
        suite.addTests(loader.loadTestsFromTestCase(ApproxAlignmentTest))
    except Exception:
        print("ApproxAlignmentTest import failed!")
        failed += 1

if "TestGeneticMiner" in enabled_tests:
    try:
        from tests.geneticminer_test import TestGeneticMiner
        suite.addTests(loader.loadTestsFromTestCase(TestGeneticMiner))
    except Exception:
        print("TestGeneticMiner import failed!")
        failed += 1

if "Ocel2CsvTest" in enabled_tests:
    try:
        from tests.ocel2_csv_test import Ocel2CsvTest
        suite.addTests(loader.loadTestsFromTestCase(Ocel2CsvTest))
    except Exception:
        print("Ocel2CsvTest import failed!")
        failed += 1

if "Ocel2GzipTest" in enabled_tests:
    try:
        from tests.ocel2_gzip_test import Ocel2GzipTest
        suite.addTests(loader.loadTestsFromTestCase(Ocel2GzipTest))
    except Exception:
        print("Ocel2GzipTest import failed!")
        failed += 1

if "OcelOlapTest" in enabled_tests:
    try:
        from tests.ocel_olap_test import OcelOlapTest
        suite.addTests(loader.loadTestsFromTestCase(OcelOlapTest))
    except Exception:
        print("OcelOlapTest import failed!")
        failed += 1

if "SimulationTest" in enabled_tests:
    try:
        from tests.simulation_test import SimulationTest
        suite.addTests(loader.loadTestsFromTestCase(SimulationTest))
    except Exception:
        print("SimulationTest import failed!")
        failed += 1

if "TraceEncodingsTest" in enabled_tests:
    try:
        from tests.trace_encodings_test import TraceEncodingsTest
        suite.addTests(loader.loadTestsFromTestCase(TraceEncodingsTest))
    except Exception:
        print("TraceEncodingsTest import failed!")
        failed += 1

if "SplitMinerInternalsTest" in enabled_tests:
    try:
        from tests.split_miner_internals_test import SplitMinerInternalsTest
        suite.addTests(loader.loadTestsFromTestCase(SplitMinerInternalsTest))
    except Exception:
        print("SplitMinerInternalsTest import failed!")
        failed += 1

if "ExtendedCoverageTest" in enabled_tests:
    try:
        from tests.extended_coverage_test import ExtendedCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(ExtendedCoverageTest))
    except Exception:
        print("ExtendedCoverageTest import failed!")
        failed += 1

if "CoverageRegressionTest" in enabled_tests:
    try:
        from tests.coverage_regression_test import CoverageRegressionTest
        suite.addTests(loader.loadTestsFromTestCase(CoverageRegressionTest))
    except Exception:
        print("CoverageRegressionTest import failed!")
        failed += 1

if "ModelUtilitiesCoverageTest" in enabled_tests:
    try:
        from tests.model_utilities_coverage_test import ModelUtilitiesCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(ModelUtilitiesCoverageTest))
    except Exception:
        print("ModelUtilitiesCoverageTest import failed!")
        failed += 1

if "GraphAnalysisCoverageTest" in enabled_tests:
    try:
        from tests.graph_analysis_coverage_test import GraphAnalysisCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(GraphAnalysisCoverageTest))
    except Exception:
        print("GraphAnalysisCoverageTest import failed!")
        failed += 1

if "LogAlgorithmsCoverageTest" in enabled_tests:
    try:
        from tests.log_algorithms_coverage_test import LogAlgorithmsCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(LogAlgorithmsCoverageTest))
    except Exception:
        print("LogAlgorithmsCoverageTest import failed!")
        failed += 1

if "PrivacyCoverageTest" in enabled_tests:
    try:
        from tests.privacy_coverage_test import PrivacyCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(PrivacyCoverageTest))
    except Exception:
        print("PrivacyCoverageTest import failed!")
        failed += 1

if "PetriNetExtraCoverageTest" in enabled_tests:
    try:
        from tests.petri_net_extra_coverage_test import PetriNetExtraCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(PetriNetExtraCoverageTest))
    except Exception:
        print("PetriNetExtraCoverageTest import failed!")
        failed += 1

if "OcelDeepCoverageTest" in enabled_tests:
    try:
        from tests.ocel_deep_coverage_test import OcelDeepCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(OcelDeepCoverageTest))
    except Exception:
        print("OcelDeepCoverageTest import failed!")
        failed += 1

if "PowlDiscoveryCoverageTest" in enabled_tests:
    try:
        from tests.powl_discovery_coverage_test import PowlDiscoveryCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(PowlDiscoveryCoverageTest))
    except Exception:
        print("PowlDiscoveryCoverageTest import failed!")
        failed += 1

if "ConnectorsCoverageTest" in enabled_tests:
    try:
        from tests.connectors_coverage_test import ConnectorsCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(ConnectorsCoverageTest))
    except Exception:
        print("ConnectorsCoverageTest import failed!")
        failed += 1

if "LlmCoverageTest" in enabled_tests:
    try:
        from tests.llm_coverage_test import LlmCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(LlmCoverageTest))
    except Exception:
        print("LlmCoverageTest import failed!")
        failed += 1

if "ClusteringDistanceCoverageTest" in enabled_tests:
    try:
        from tests.clustering_distance_coverage_test import ClusteringDistanceCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(ClusteringDistanceCoverageTest))
    except Exception:
        print("ClusteringDistanceCoverageTest import failed!")
        failed += 1

if "VisualPerformanceCoverageTest" in enabled_tests:
    try:
        from tests.visual_performance_coverage_test import VisualPerformanceCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(VisualPerformanceCoverageTest))
    except Exception:
        print("VisualPerformanceCoverageTest import failed!")
        failed += 1

if "XesDeepCoverageTest" in enabled_tests:
    try:
        from tests.xes_deep_coverage_test import XesDeepCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(XesDeepCoverageTest))
    except Exception:
        print("XesDeepCoverageTest import failed!")
        failed += 1

if "BpmnDeepCoverageTest" in enabled_tests:
    try:
        from tests.bpmn_deep_coverage_test import BpmnDeepCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(BpmnDeepCoverageTest))
    except Exception:
        print("BpmnDeepCoverageTest import failed!")
        failed += 1

if "FacadeUtilsCoverageTest" in enabled_tests:
    try:
        from tests.facade_utils_coverage_test import FacadeUtilsCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(FacadeUtilsCoverageTest))
    except Exception:
        print("FacadeUtilsCoverageTest import failed!")
        failed += 1

if "ProcessTreePetriDeepCoverageTest" in enabled_tests:
    try:
        from tests.process_tree_petri_deep_coverage_test import ProcessTreePetriDeepCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(ProcessTreePetriDeepCoverageTest))
    except Exception:
        print("ProcessTreePetriDeepCoverageTest import failed!")
        failed += 1

if "ConformanceDecisionDeepCoverageTest" in enabled_tests:
    try:
        from tests.conformance_decision_deep_coverage_test import ConformanceDecisionDeepCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(ConformanceDecisionDeepCoverageTest))
    except Exception:
        print("ConformanceDecisionDeepCoverageTest import failed!")
        failed += 1

if "MiscSubsystemsCoverageTest" in enabled_tests:
    try:
        from tests.misc_subsystems_coverage_test import MiscSubsystemsCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(MiscSubsystemsCoverageTest))
    except Exception:
        print("MiscSubsystemsCoverageTest import failed!")
        failed += 1

if "VisualizationFacadeDeepCoverageTest" in enabled_tests:
    try:
        from tests.visualization_facade_deep_coverage_test import VisualizationFacadeDeepCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(VisualizationFacadeDeepCoverageTest))
    except Exception:
        print("VisualizationFacadeDeepCoverageTest import failed!")
        failed += 1

if "SerializationLogUtilsCoverageTest" in enabled_tests:
    try:
        from tests.serialization_log_utils_coverage_test import SerializationLogUtilsCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(SerializationLogUtilsCoverageTest))
    except:
        print("SerializationLogUtilsCoverageTest import failed!")
        failed += 1

if "PetriStochasticSerializationCoverageTest" in enabled_tests:
    try:
        from tests.petri_stochastic_serialization_coverage_test import PetriStochasticSerializationCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(PetriStochasticSerializationCoverageTest))
    except:
        print("PetriStochasticSerializationCoverageTest import failed!")
        failed += 1

if "PolarsAnalyticsDeepCoverageTest" in enabled_tests:
    try:
        from tests.polars_analytics_deep_coverage_test import PolarsAnalyticsDeepCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(PolarsAnalyticsDeepCoverageTest))
    except:
        print("PolarsAnalyticsDeepCoverageTest import failed!")
        failed += 1

if "PowlTreeGenerationDeepCoverageTest" in enabled_tests:
    try:
        from tests.powl_tree_generation_deep_coverage_test import PowlTreeGenerationDeepCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(PowlTreeGenerationDeepCoverageTest))
    except:
        print("PowlTreeGenerationDeepCoverageTest import failed!")
        failed += 1

if "RemainingAlgorithmsCoverageTest" in enabled_tests:
    try:
        from tests.remaining_algorithms_coverage_test import RemainingAlgorithmsCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(RemainingAlgorithmsCoverageTest))
    except Exception:
        print("RemainingAlgorithmsCoverageTest import failed!")
        failed += 1

if "IoFilteringEdgeCoverageTest" in enabled_tests:
    try:
        from tests.io_filtering_edge_coverage_test import IoFilteringEdgeCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(IoFilteringEdgeCoverageTest))
    except Exception:
        print("IoFilteringEdgeCoverageTest import failed!")
        failed += 1

if "FinalBufferCoverageTest" in enabled_tests:
    try:
        from tests.final_buffer_coverage_test import FinalBufferCoverageTest
        suite.addTests(loader.loadTestsFromTestCase(FinalBufferCoverageTest))
    except Exception:
        print("FinalBufferCoverageTest import failed!")
        failed += 1

# If some imports failed, let's wait a little bit
if failed > 0:
    time.sleep(7.5)


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--pipeline', action='store_true')

    args = parser.parse_args()
    return args.pipeline


def main():
    if EXECUTE_TESTS:
        in_pipeline = parse_args()
        test_config.IS_PIPELINE_RUN = in_pipeline

        runner = unittest.TextTestRunner()
        result = runner.run(suite)

        # Count test-level failures
        test_failures = len(result.failures)
        test_errors = len(result.errors)
        test_skipped = len(result.skipped)
        test_runs = result.testsRun - test_skipped # apparently skipped tests count as successfully run tests

        # The number of actual test-method-level fails
        test_level_failed = test_failures + test_errors
        test_level_passed = test_runs - test_level_failed

        # Incorporate import-level failures. Treat each import failure as one "failed test" for simplicity.
        total_tests_including_imports = test_runs + failed
        total_fails_including_imports = test_level_failed + failed
        total_pass_including_imports = total_tests_including_imports - total_fails_including_imports

        # Compute pass ratio (avoid division by zero)
        if total_tests_including_imports > 0:
            pass_ratio = total_pass_including_imports / total_tests_including_imports
        else:
            pass_ratio = 0.0

        print("\n--- Summary ---")
        print(f"Import failures: {failed}")
        print(f"Test methods run: {test_runs}")
        print(f"Test-level passed: {test_level_passed}")
        print(f"Test-level failed: {test_level_failed}")
        print(f"Total tests (including import fails): {total_tests_including_imports}")
        print(f"Total passed (including import fails): {total_pass_including_imports}")
        print(f"Total failed (including import fails): {total_fails_including_imports}")
        print(f"Total skipped: {test_skipped}")
        print(f"Overall pass ratio: {round(pass_ratio * 100, 2)}%")

    # Print library versions
    print("numpy version: " + str(numpy.__version__))
    print("pandas version: " + str(pandas.__version__))
    print("networkx version: " + str(networkx.__version__))

    if importlib.util.find_spec("scipy"):
        import scipy
        print("scipy version: " + str(scipy.__version__))

    if importlib.util.find_spec("lxml"):
        import lxml
        print("lxml version: " + str(lxml.__version__))

    if importlib.util.find_spec("matplotlib"):
        import matplotlib
        print("matplotlib version: " + str(matplotlib.__version__))

    if importlib.util.find_spec("sklearn"):
        import sklearn
        print("sklearn version: " + str(sklearn.__version__))

    print("pm4py version: " + str(pm4py.__version__))
    print("Python version: " + str(sys.version))

    # Exit code logic: 0 if pass ratio is 100%, else 1
    if EXECUTE_TESTS and pass_ratio == 1:
        #print("exiting with system code 0")
        sys.exit(0)
    else:
        #print("exiting with system code 1")
        sys.exit(1)


if __name__ == "__main__":
    main()
