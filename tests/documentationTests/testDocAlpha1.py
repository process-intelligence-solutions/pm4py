import unittest
import os,sys,inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
parentdir2 = os.path.dirname(parentdir)
sys.path.insert(0,parentdir)
sys.path.insert(0,parentdir2)

class AlphaMinerDocumentationTest(unittest.TestCase):
	def test_alphadoc1(self):
		from pm4py.log.importer import xes_importer as xes_importer
		log = xes_importer.import_from_file_xes("inputData\\running-example.xes")
		from pm4py.algo.alpha import factory as alpha_miner
		net, initial_marking, final_marking = alpha_miner.apply(log)
		from pm4py.models.petri import visualize as pn_viz
		gviz = pn_viz.graphviz_visualization(net, initial_marking=initial_marking, final_marking=final_marking)
		#gviz.view()

if __name__ == "__main__":
	unittest.main()