import unittest
from pm4py.visualization.footprints.variants import comparison_symmetric
from graphviz import Source


class ComparisonSymmetricTest(unittest.TestCase):

    def test_equal_footprints(self):
        """Visualization when both footprints are equal"""

        # Arrange
        fp1 = {
            "sequence": [("A", "B"), ("B", "C")],
            "parallel": [("D", "E")]
        }
        fp2 = {
            "sequence": [("A", "B"), ("B", "C")],
            "parallel": [("D", "E")]
        }
        
        # Act
        result = comparison_symmetric.apply(fp1, fp2)
        
        # Assert
        self.assertIsInstance(result, Source, "Result is a Graphviz object")
        self.assertIn("digraph", result.source, "Result contains digraph declaration")
        self.assertIn("black", result.source, "Matching footprints use black color")
        self.assertNotIn("red", result.source, "Does not use red color")

    def test_different_footprints(self):
        """Visualization when footprints are not equal"""
        # Arrange
        fp1 = {
            "sequence": [("A", "B")],
            "parallel": []
        }
        fp2 = {
            "sequence": [("A", "C")],
            "parallel": []
        }
        parameters = {comparison_symmetric.Parameters.FORMAT: "svg"}

        # Act
        result = comparison_symmetric.apply(fp1, fp2, parameters=parameters)
        
        # Assert
        self.assertIsInstance(result, Source, "Result is a Graphviz Source object")
        self.assertEqual("svg", result.format, "Format should be set to svg")
        self.assertIn("table", result.source, "Result contains table structure")
        self.assertIn("red", result.source, "Red color for differences")

    def test_list_footprint_raises_exception(self):
        """Passing a list as footprint should raise an exception"""
        # Arrange
        fp_list = [{"sequence": [("A", "B")], "parallel": []}]
        fp_valid = {"sequence": [("A", "B")], "parallel": []}

        # Act & Assert
        with self.assertRaises(Exception) as context:
            comparison_symmetric.apply(fp_list, fp_valid)
        
        self.assertIn("function does not work on list, has to be dictionary", str(context.exception))

        # Test with second parameter as list
        with self.assertRaises(Exception) as context2:
            comparison_symmetric.apply(fp_valid, fp_list)
        
        self.assertIn("function does not work on list, has to be dictionary", str(context2.exception))

    def test_graph_title_enabled(self):
        """Visualization with graph title enabled"""
        # Arrange
        fp1 = {"sequence": [("A", "B")], "parallel": []}
        fp2 = {"sequence": [("A", "B")], "parallel": []}
        custom_title = "Title"
        parameters = {
            comparison_symmetric.Parameters.ENABLE_GRAPH_TITLE: True,
            comparison_symmetric.Parameters.GRAPH_TITLE: custom_title
        }

        # Act
        result = comparison_symmetric.apply(fp1, fp2, parameters=parameters)
        
        # Assert
        self.assertIsInstance(result, Source, "Result should be a Graphviz object")
        self.assertIn(custom_title, result.source, "Result should contain custom title")
        self.assertIn("labelloc", result.source, "Graph has label location set")


if __name__ == "__main__":
    unittest.main()
