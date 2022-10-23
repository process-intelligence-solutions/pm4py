import runpy
from os.path import dirname, join
from pathlib import Path
from setuptools import setup


# Import only the metadata of the pm4py to use in the setup. We cannot import it directly because
# then we need to import packages that are about to be installed by the setup itself.
meta_path = Path(__file__).parent.absolute() / "pm4py" / "meta.py"
meta = runpy.run_path(str(meta_path))


def read_file(filename):
    with open(join(dirname(__file__), filename)) as f:
        return f.read()


setup(
    name=meta['__name__'],
    version=meta['__version__'],
    description=meta['__doc__'].strip(),
    long_description=read_file('README.md'),
    author=meta['__author__'],
    author_email=meta['__author_email__'],
    py_modules=['pm4py'],
    include_package_data=True,
    packages=['pm4py', 'pm4py.algo', 'pm4py.algo.merging', 'pm4py.algo.merging.case_relations',
              'pm4py.algo.merging.case_relations.variants', 'pm4py.algo.analysis', 'pm4py.algo.analysis.woflan',
              'pm4py.algo.analysis.woflan.graphs', 'pm4py.algo.analysis.woflan.graphs.reachability_graph',
              'pm4py.algo.analysis.woflan.graphs.minimal_coverability_graph',
              'pm4py.algo.analysis.woflan.graphs.restricted_coverability_graph',
              'pm4py.algo.analysis.woflan.place_invariants', 'pm4py.algo.analysis.woflan.not_well_handled_pairs',
              'pm4py.algo.analysis.workflow_net', 'pm4py.algo.analysis.workflow_net.variants',
              'pm4py.algo.analysis.marking_equation', 'pm4py.algo.analysis.marking_equation.variants',
              'pm4py.algo.analysis.extended_marking_equation', 'pm4py.algo.analysis.extended_marking_equation.variants',
              'pm4py.algo.discovery', 'pm4py.algo.discovery.dfg', 'pm4py.algo.discovery.dfg.utils',
              'pm4py.algo.discovery.dfg.adapters', 'pm4py.algo.discovery.dfg.adapters.pandas',
              'pm4py.algo.discovery.dfg.variants', 'pm4py.algo.discovery.ocel', 'pm4py.algo.discovery.ocel.ocpn',
              'pm4py.algo.discovery.ocel.ocpn.variants', 'pm4py.algo.discovery.ocel.ocdfg',
              'pm4py.algo.discovery.ocel.ocdfg.variants', 'pm4py.algo.discovery.ocel.interleavings',
              'pm4py.algo.discovery.ocel.interleavings.utils', 'pm4py.algo.discovery.ocel.interleavings.variants',
              'pm4py.algo.discovery.ocel.link_analysis', 'pm4py.algo.discovery.ocel.link_analysis.variants',
              'pm4py.algo.discovery.alpha', 'pm4py.algo.discovery.alpha.utils', 'pm4py.algo.discovery.alpha.variants',
              'pm4py.algo.discovery.alpha.data_structures', 'pm4py.algo.discovery.causal',
              'pm4py.algo.discovery.causal.variants', 'pm4py.algo.discovery.batches',
              'pm4py.algo.discovery.batches.utils', 'pm4py.algo.discovery.batches.variants',
              'pm4py.algo.discovery.inductive', 'pm4py.algo.discovery.inductive.cuts',
              'pm4py.algo.discovery.inductive.dtypes', 'pm4py.algo.discovery.inductive.variants',
              'pm4py.algo.discovery.inductive.base_case', 'pm4py.algo.discovery.inductive.fall_through',
              'pm4py.algo.discovery.footprints', 'pm4py.algo.discovery.footprints.dfg',
              'pm4py.algo.discovery.footprints.dfg.variants', 'pm4py.algo.discovery.footprints.log',
              'pm4py.algo.discovery.footprints.log.variants', 'pm4py.algo.discovery.footprints.tree',
              'pm4py.algo.discovery.footprints.tree.variants', 'pm4py.algo.discovery.footprints.petri',
              'pm4py.algo.discovery.footprints.petri.variants', 'pm4py.algo.discovery.heuristics',
              'pm4py.algo.discovery.heuristics.variants', 'pm4py.algo.discovery.log_skeleton',
              'pm4py.algo.discovery.log_skeleton.variants', 'pm4py.algo.discovery.temporal_profile',
              'pm4py.algo.discovery.temporal_profile.variants', 'pm4py.algo.discovery.transition_system',
              'pm4py.algo.discovery.transition_system.variants', 'pm4py.algo.discovery.correlation_mining',
              'pm4py.algo.discovery.correlation_mining.variants', 'pm4py.algo.discovery.performance_spectrum',
              'pm4py.algo.discovery.performance_spectrum.variants', 'pm4py.algo.discovery.minimum_self_distance',
              'pm4py.algo.discovery.minimum_self_distance.variants', 'pm4py.algo.filtering', 'pm4py.algo.filtering.dfg',
              'pm4py.algo.filtering.log', 'pm4py.algo.filtering.log.ltl', 'pm4py.algo.filtering.log.cases',
              'pm4py.algo.filtering.log.paths', 'pm4py.algo.filtering.log.rework', 'pm4py.algo.filtering.log.between',
              'pm4py.algo.filtering.log.prefixes', 'pm4py.algo.filtering.log.suffixes',
              'pm4py.algo.filtering.log.variants', 'pm4py.algo.filtering.log.timestamp',
              'pm4py.algo.filtering.log.attributes', 'pm4py.algo.filtering.log.end_activities',
              'pm4py.algo.filtering.log.start_activities', 'pm4py.algo.filtering.log.attr_value_repetition',
              'pm4py.algo.filtering.ocel', 'pm4py.algo.filtering.common', 'pm4py.algo.filtering.common.timestamp',
              'pm4py.algo.filtering.common.attributes', 'pm4py.algo.filtering.common.end_activities',
              'pm4py.algo.filtering.common.start_activities', 'pm4py.algo.filtering.pandas',
              'pm4py.algo.filtering.pandas.ltl', 'pm4py.algo.filtering.pandas.cases',
              'pm4py.algo.filtering.pandas.paths', 'pm4py.algo.filtering.pandas.rework',
              'pm4py.algo.filtering.pandas.traces', 'pm4py.algo.filtering.pandas.between',
              'pm4py.algo.filtering.pandas.prefixes', 'pm4py.algo.filtering.pandas.suffixes',
              'pm4py.algo.filtering.pandas.variants', 'pm4py.algo.filtering.pandas.ends_with',
              'pm4py.algo.filtering.pandas.timestamp', 'pm4py.algo.filtering.pandas.attributes',
              'pm4py.algo.filtering.pandas.starts_with', 'pm4py.algo.filtering.pandas.end_activities',
              'pm4py.algo.filtering.pandas.start_activities', 'pm4py.algo.filtering.pandas.attr_value_repetition',
              'pm4py.algo.reduction', 'pm4py.algo.reduction.process_tree', 'pm4py.algo.reduction.process_tree.variants',
              'pm4py.algo.clustering', 'pm4py.algo.clustering.trace_attribute_driven',
              'pm4py.algo.clustering.trace_attribute_driven.dfg', 'pm4py.algo.clustering.trace_attribute_driven.util',
              'pm4py.algo.clustering.trace_attribute_driven.variants',
              'pm4py.algo.clustering.trace_attribute_driven.merge_log',
              'pm4py.algo.clustering.trace_attribute_driven.leven_dist',
              'pm4py.algo.clustering.trace_attribute_driven.linkage_method', 'pm4py.algo.comparison',
              'pm4py.algo.comparison.petrinet', 'pm4py.algo.evaluation', 'pm4py.algo.evaluation.precision',
              'pm4py.algo.evaluation.precision.dfg', 'pm4py.algo.evaluation.precision.variants',
              'pm4py.algo.evaluation.simplicity', 'pm4py.algo.evaluation.simplicity.variants',
              'pm4py.algo.evaluation.generalization', 'pm4py.algo.evaluation.generalization.variants',
              'pm4py.algo.evaluation.replay_fitness', 'pm4py.algo.evaluation.replay_fitness.variants',
              'pm4py.algo.evaluation.earth_mover_distance', 'pm4py.algo.evaluation.earth_mover_distance.variants',
              'pm4py.algo.simulation', 'pm4py.algo.simulation.playout', 'pm4py.algo.simulation.playout.dfg',
              'pm4py.algo.simulation.playout.dfg.variants', 'pm4py.algo.simulation.playout.petri_net',
              'pm4py.algo.simulation.playout.petri_net.variants', 'pm4py.algo.simulation.playout.process_tree',
              'pm4py.algo.simulation.playout.process_tree.variants', 'pm4py.algo.simulation.montecarlo',
              'pm4py.algo.simulation.montecarlo.utils', 'pm4py.algo.simulation.montecarlo.variants',
              'pm4py.algo.simulation.tree_generator', 'pm4py.algo.simulation.tree_generator.variants',
              'pm4py.algo.conformance', 'pm4py.algo.conformance.alignments', 'pm4py.algo.conformance.alignments.dfg',
              'pm4py.algo.conformance.alignments.dfg.variants', 'pm4py.algo.conformance.alignments.petri_net',
              'pm4py.algo.conformance.alignments.petri_net.utils',
              'pm4py.algo.conformance.alignments.petri_net.variants', 'pm4py.algo.conformance.alignments.decomposed',
              'pm4py.algo.conformance.alignments.decomposed.variants', 'pm4py.algo.conformance.alignments.process_tree',
              'pm4py.algo.conformance.alignments.process_tree.util',
              'pm4py.algo.conformance.alignments.process_tree.variants',
              'pm4py.algo.conformance.alignments.process_tree.variants.approximated',
              'pm4py.algo.conformance.alignments.edit_distance',
              'pm4py.algo.conformance.alignments.edit_distance.variants', 'pm4py.algo.conformance.footprints',
              'pm4py.algo.conformance.footprints.util', 'pm4py.algo.conformance.footprints.variants',
              'pm4py.algo.conformance.tokenreplay', 'pm4py.algo.conformance.tokenreplay.variants',
              'pm4py.algo.conformance.tokenreplay.diagnostics', 'pm4py.algo.conformance.log_skeleton',
              'pm4py.algo.conformance.log_skeleton.variants', 'pm4py.algo.conformance.antialignments',
              'pm4py.algo.conformance.antialignments.variants', 'pm4py.algo.conformance.multialignments',
              'pm4py.algo.conformance.multialignments.variants', 'pm4py.algo.conformance.temporal_profile',
              'pm4py.algo.conformance.temporal_profile.variants', 'pm4py.algo.transformation',
              'pm4py.algo.transformation.ocel', 'pm4py.algo.transformation.ocel.graphs',
              'pm4py.algo.transformation.ocel.features', 'pm4py.algo.transformation.ocel.features.events',
              'pm4py.algo.transformation.ocel.features.objects',
              'pm4py.algo.transformation.ocel.features.events_objects', 'pm4py.algo.transformation.ocel.split_ocel',
              'pm4py.algo.transformation.ocel.split_ocel.variants', 'pm4py.algo.transformation.log_to_trie',
              'pm4py.algo.transformation.log_to_features', 'pm4py.algo.transformation.log_to_features.util',
              'pm4py.algo.transformation.log_to_features.variants', 'pm4py.algo.transformation.log_to_interval_tree',
              'pm4py.algo.transformation.log_to_interval_tree.variants', 'pm4py.algo.decision_mining',
              'pm4py.algo.organizational_mining', 'pm4py.algo.organizational_mining.sna',
              'pm4py.algo.organizational_mining.sna.variants', 'pm4py.algo.organizational_mining.sna.variants.log',
              'pm4py.algo.organizational_mining.sna.variants.pandas', 'pm4py.algo.organizational_mining.roles',
              'pm4py.algo.organizational_mining.roles.common', 'pm4py.algo.organizational_mining.roles.variants',
              'pm4py.algo.organizational_mining.network_analysis',
              'pm4py.algo.organizational_mining.network_analysis.variants',
              'pm4py.algo.organizational_mining.local_diagnostics',
              'pm4py.algo.organizational_mining.resource_profiles',
              'pm4py.algo.organizational_mining.resource_profiles.variants', 'pm4py.util', 'pm4py.util.lp',
              'pm4py.util.lp.util', 'pm4py.util.lp.variants', 'pm4py.util.dt_parsing', 'pm4py.util.dt_parsing.variants',
              'pm4py.util.compression', 'pm4py.objects', 'pm4py.objects.dfg', 'pm4py.objects.dfg.utils',
              'pm4py.objects.dfg.exporter', 'pm4py.objects.dfg.exporter.variants', 'pm4py.objects.dfg.importer',
              'pm4py.objects.dfg.importer.variants', 'pm4py.objects.dfg.filtering', 'pm4py.objects.dfg.retrieval',
              'pm4py.objects.log', 'pm4py.objects.log.util', 'pm4py.objects.log.exporter',
              'pm4py.objects.log.exporter.xes', 'pm4py.objects.log.exporter.xes.util',
              'pm4py.objects.log.exporter.xes.variants', 'pm4py.objects.log.importer', 'pm4py.objects.log.importer.xes',
              'pm4py.objects.log.importer.xes.variants', 'pm4py.objects.org', 'pm4py.objects.org.sna',
              'pm4py.objects.org.roles', 'pm4py.objects.bpmn', 'pm4py.objects.bpmn.util', 'pm4py.objects.bpmn.layout',
              'pm4py.objects.bpmn.layout.variants', 'pm4py.objects.bpmn.exporter',
              'pm4py.objects.bpmn.exporter.variants', 'pm4py.objects.bpmn.importer',
              'pm4py.objects.bpmn.importer.variants', 'pm4py.objects.ocel', 'pm4py.objects.ocel.util',
              'pm4py.objects.ocel.exporter', 'pm4py.objects.ocel.exporter.csv',
              'pm4py.objects.ocel.exporter.csv.variants', 'pm4py.objects.ocel.exporter.util',
              'pm4py.objects.ocel.exporter.xmlocel', 'pm4py.objects.ocel.exporter.xmlocel.variants',
              'pm4py.objects.ocel.exporter.jsonocel', 'pm4py.objects.ocel.exporter.jsonocel.variants',
              'pm4py.objects.ocel.importer', 'pm4py.objects.ocel.importer.csv',
              'pm4py.objects.ocel.importer.csv.variants', 'pm4py.objects.ocel.importer.xmlocel',
              'pm4py.objects.ocel.importer.xmlocel.variants', 'pm4py.objects.ocel.importer.jsonocel',
              'pm4py.objects.ocel.importer.jsonocel.variants', 'pm4py.objects.ocel.validation', 'pm4py.objects.trie',
              'pm4py.objects.petri_net', 'pm4py.objects.petri_net.utils', 'pm4py.objects.petri_net.exporter',
              'pm4py.objects.petri_net.exporter.variants', 'pm4py.objects.petri_net.importer',
              'pm4py.objects.petri_net.importer.variants', 'pm4py.objects.petri_net.data_petri_nets',
              'pm4py.objects.petri_net.inhibitor_reset', 'pm4py.objects.conversion', 'pm4py.objects.conversion.dfg',
              'pm4py.objects.conversion.dfg.variants', 'pm4py.objects.conversion.log',
              'pm4py.objects.conversion.log.variants', 'pm4py.objects.conversion.bpmn',
              'pm4py.objects.conversion.bpmn.variants', 'pm4py.objects.conversion.wf_net',
              'pm4py.objects.conversion.wf_net.variants', 'pm4py.objects.conversion.process_tree',
              'pm4py.objects.conversion.process_tree.variants', 'pm4py.objects.conversion.heuristics_net',
              'pm4py.objects.conversion.heuristics_net.variants', 'pm4py.objects.process_tree',
              'pm4py.objects.process_tree.utils', 'pm4py.objects.process_tree.exporter',
              'pm4py.objects.process_tree.exporter.variants', 'pm4py.objects.process_tree.importer',
              'pm4py.objects.process_tree.importer.variants', 'pm4py.objects.heuristics_net',
              'pm4py.objects.random_variables', 'pm4py.objects.random_variables.gamma',
              'pm4py.objects.random_variables.normal', 'pm4py.objects.random_variables.uniform',
              'pm4py.objects.random_variables.constant0', 'pm4py.objects.random_variables.lognormal',
              'pm4py.objects.random_variables.exponential', 'pm4py.objects.stochastic_petri',
              'pm4py.objects.transition_system', 'pm4py.streaming', 'pm4py.streaming.algo',
              'pm4py.streaming.algo.discovery', 'pm4py.streaming.algo.discovery.dfg',
              'pm4py.streaming.algo.discovery.dfg.variants', 'pm4py.streaming.algo.conformance',
              'pm4py.streaming.algo.conformance.tbr', 'pm4py.streaming.algo.conformance.tbr.variants',
              'pm4py.streaming.algo.conformance.temporal', 'pm4py.streaming.algo.conformance.temporal.variants',
              'pm4py.streaming.algo.conformance.footprints', 'pm4py.streaming.algo.conformance.footprints.variants',
              'pm4py.streaming.util', 'pm4py.streaming.util.dictio', 'pm4py.streaming.util.dictio.versions',
              'pm4py.streaming.stream', 'pm4py.streaming.importer', 'pm4py.streaming.importer.csv',
              'pm4py.streaming.importer.csv.variants', 'pm4py.streaming.importer.xes',
              'pm4py.streaming.importer.xes.variants', 'pm4py.streaming.conversion', 'pm4py.statistics',
              'pm4py.statistics.ocel', 'pm4py.statistics.util', 'pm4py.statistics.rework',
              'pm4py.statistics.rework.log', 'pm4py.statistics.rework.cases', 'pm4py.statistics.rework.cases.log',
              'pm4py.statistics.rework.cases.pandas', 'pm4py.statistics.rework.pandas', 'pm4py.statistics.traces',
              'pm4py.statistics.traces.generic', 'pm4py.statistics.traces.generic.log',
              'pm4py.statistics.traces.generic.common', 'pm4py.statistics.traces.generic.pandas',
              'pm4py.statistics.traces.cycle_time', 'pm4py.statistics.traces.cycle_time.log',
              'pm4py.statistics.traces.cycle_time.util', 'pm4py.statistics.traces.cycle_time.pandas',
              'pm4py.statistics.overlap', 'pm4py.statistics.overlap.cases', 'pm4py.statistics.overlap.cases.log',
              'pm4py.statistics.overlap.cases.pandas', 'pm4py.statistics.overlap.utils',
              'pm4py.statistics.overlap.interval_events', 'pm4py.statistics.overlap.interval_events.log',
              'pm4py.statistics.overlap.interval_events.pandas', 'pm4py.statistics.variants',
              'pm4py.statistics.variants.log', 'pm4py.statistics.variants.pandas', 'pm4py.statistics.attributes',
              'pm4py.statistics.attributes.log', 'pm4py.statistics.attributes.common',
              'pm4py.statistics.attributes.pandas', 'pm4py.statistics.passed_time', 'pm4py.statistics.passed_time.log',
              'pm4py.statistics.passed_time.log.variants', 'pm4py.statistics.passed_time.pandas',
              'pm4py.statistics.passed_time.pandas.variants', 'pm4py.statistics.sojourn_time',
              'pm4py.statistics.sojourn_time.log', 'pm4py.statistics.sojourn_time.pandas',
              'pm4py.statistics.end_activities', 'pm4py.statistics.end_activities.log',
              'pm4py.statistics.end_activities.common', 'pm4py.statistics.end_activities.pandas',
              'pm4py.statistics.start_activities', 'pm4py.statistics.start_activities.log',
              'pm4py.statistics.start_activities.common', 'pm4py.statistics.start_activities.pandas',
              'pm4py.statistics.eventually_follows', 'pm4py.statistics.eventually_follows.log',
              'pm4py.statistics.eventually_follows.pandas', 'pm4py.statistics.concurrent_activities',
              'pm4py.statistics.concurrent_activities.log', 'pm4py.statistics.concurrent_activities.pandas',
              'pm4py.visualization', 'pm4py.visualization.dfg', 'pm4py.visualization.dfg.variants',
              'pm4py.visualization.sna', 'pm4py.visualization.sna.variants', 'pm4py.visualization.bpmn',
              'pm4py.visualization.bpmn.variants', 'pm4py.visualization.ocel', 'pm4py.visualization.ocel.ocpn',
              'pm4py.visualization.ocel.ocpn.variants', 'pm4py.visualization.ocel.ocdfg',
              'pm4py.visualization.ocel.ocdfg.variants', 'pm4py.visualization.ocel.object_graph',
              'pm4py.visualization.ocel.object_graph.variants', 'pm4py.visualization.ocel.interleavings',
              'pm4py.visualization.ocel.interleavings.variants', 'pm4py.visualization.trie',
              'pm4py.visualization.trie.variants', 'pm4py.visualization.common', 'pm4py.visualization.graphs',
              'pm4py.visualization.graphs.util', 'pm4py.visualization.graphs.variants', 'pm4py.visualization.petri_net',
              'pm4py.visualization.petri_net.util', 'pm4py.visualization.petri_net.common',
              'pm4py.visualization.petri_net.variants', 'pm4py.visualization.footprints',
              'pm4py.visualization.footprints.variants', 'pm4py.visualization.align_table',
              'pm4py.visualization.align_table.variants', 'pm4py.visualization.decisiontree',
              'pm4py.visualization.decisiontree.util', 'pm4py.visualization.decisiontree.variants',
              'pm4py.visualization.dotted_chart', 'pm4py.visualization.dotted_chart.variants',
              'pm4py.visualization.process_tree', 'pm4py.visualization.process_tree.variants',
              'pm4py.visualization.heuristics_net', 'pm4py.visualization.heuristics_net.variants',
              'pm4py.visualization.network_analysis', 'pm4py.visualization.network_analysis.variants',
              'pm4py.visualization.transition_system', 'pm4py.visualization.transition_system.util',
              'pm4py.visualization.transition_system.variants', 'pm4py.visualization.performance_spectrum',
              'pm4py.visualization.performance_spectrum.variants'],
    url='http://www.pm4py.org',
    license='GPL 3.0',
    install_requires=read_file("requirements.txt").split("\n"),
    project_urls={
        'Documentation': 'http://www.pm4py.org',
        'Source': 'https://github.com/pm4py/pm4py-source',
        'Tracker': 'https://github.com/pm4py/pm4py-source/issues',
    }
)
