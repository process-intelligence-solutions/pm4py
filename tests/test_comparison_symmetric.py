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


if __name__ == "__main__":
    unittest.main()
