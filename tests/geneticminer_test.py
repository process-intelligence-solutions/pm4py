#!/usr/bin/env python3 -m unittest tests.geneticminer_test
# Author: Maximilian Josef Frank (https://orcid.org/0000-0002-0714-7748)

import random
import unittest
from pm4py import save_vis_petri_net
from pm4py.algo.discovery.genetic.util import iset
from pm4py.algo.discovery.genetic.variants.classic import sample_parents
from pm4py.objects.conversion.genetic_matrix.variants.to_petri_net import apply as matrix2petrinet
from pm4py.objects.genetic_matrix.obj import GeneticMatrix
from pm4py.objects.petri_net.obj import PetriNet
from pm4py.objects.petri_net import utils


class TestGeneticMiner(unittest.TestCase):
        def test_sample_parents_with_duplicate_individuals(self):
                self.addCleanup(random.setstate, random.getstate())
                duplicates = [({"A": []}, {"A": []}) for _ in range(3)]
                alternative = ({"B": []}, {"B": []})

                first, second = sample_parents(
                        duplicates + [alternative], [0.9, 0.9, 0.9, 0.5], 3
                )
                self.assertEqual(first, duplicates[0])
                self.assertIs(second, alternative)

                first, second = sample_parents(duplicates, [0.9] * 3, 2)
                self.assertEqual(first, second)
                self.assertIsNot(first, second)

        def test_matrix2petrinet_or(self):
                I = {
                        "A": [],
                        "B": [{"A"}],
                        "C": [{"A"}],
                        "D": [{"B","C"}]
                }
                O = {
                        "A": [{"B","C"}],
                        "B": [{"D"}],
                        "C": [{"D"}],
                        "D": []
                }
                for t in I:
                        I[t] = [iset(s) for s in I[t]]
                        O[t] = [iset(s) for s in O[t]]
                res,_,_ = self._subject(I, O, T=I.keys())
#               self._visualise(res)
                cmp = """places: [ ({'A'}, {'B', 'C'}), ({'B', 'C'}, {'D'}), i, o ]
transitions: [ (A, 'A'), (B, 'B'), (C, 'C'), (D, 'D') ]
arcs: [ (A, 'A')->({'A'}, {'B', 'C'}), (B, 'B')->({'B', 'C'}, {'D'}), (C, 'C')->({'B', 'C'}, {'D'}), (D, 'D')->o, ({'A'}, {'B', 'C'})->(B, 'B'), ({'A'}, {'B', 'C'})->(C, 'C'), ({'B', 'C'}, {'D'})->(D, 'D'), i->(A, 'A') ]"""
                self.assertEqual(str(res), cmp, "Mismatching matrix and petri net")

        def test_matrix2petrinet_or2(self):
                I = {
                        "A": [],
                        "B": [],
                        "C": [{"A","B"}],
                        "D": [{"A","B"}]
                }
                O = {
                        "A": [{"C","D"}],
                        "B": [{"C","D"}],
                        "C": [],
                        "D": []
                }
                for t in I:
                        I[t] = [iset(s) for s in I[t]]
                        O[t] = [iset(s) for s in O[t]]
                res,_,_ = self._subject(I, O, T=I.keys())
#               self._visualise(res)
                cmp = """places: [ ({'A', 'B'}, {'C', 'D'}), i, o ]
transitions: [ (A, 'A'), (B, 'B'), (C, 'C'), (D, 'D') ]
arcs: [ (A, 'A')->({'A', 'B'}, {'C', 'D'}), (B, 'B')->({'A', 'B'}, {'C', 'D'}), (C, 'C')->o, (D, 'D')->o, ({'A', 'B'}, {'C', 'D'})->(C, 'C'), ({'A', 'B'}, {'C', 'D'})->(D, 'D'), i->(A, 'A'), i->(B, 'B') ]"""
                self.assertEqual(str(res), cmp, "Mismatching matrix and petri net")

        def test_matrix2petrinet_andOrCross(self):
                I = {
                        "A": [],
                        "B": [],
                        "C": [{"A"},{"B"}],
                        "D": [{"A","B"}]
                }
                O = {
                        "A": [{"C","D"}],
                        "B": [{"C"},{"D"}],
                        "C": [],
                        "D": []
                }
                for t in I:
                        I[t] = [iset(s) for s in I[t]]
                        O[t] = [iset(s) for s in O[t]]
                res,_,_ = self._subject(I, O, T=I.keys())
#               self._visualise(res)
                cmp = """places: [ i, i('C', {'A'}), i('C', {'B'}), i('D', {'A', 'B'}), o, o('A', {'C', 'D'}), o('B', {'C'}), o('B', {'D'}) ]
transitions: [ (, None), (, None), (, None), (, None), (A, 'A'), (B, 'B'), (C, 'C'), (D, 'D') ]
arcs: [ (, None)->i('C', {'A'}), (, None)->i('C', {'B'}), (, None)->i('D', {'A', 'B'}), (, None)->i('D', {'A', 'B'}), (A, 'A')->o('A', {'C', 'D'}), (B, 'B')->o('B', {'C'}), (B, 'B')->o('B', {'D'}), (C, 'C')->o, (D, 'D')->o, i('C', {'A'})->(C, 'C'), i('C', {'B'})->(C, 'C'), i('D', {'A', 'B'})->(D, 'D'), i->(A, 'A'), i->(B, 'B'), o('A', {'C', 'D'})->(, None), o('A', {'C', 'D'})->(, None), o('B', {'C'})->(, None), o('B', {'D'})->(, None) ]"""
                self.assertEqual(str(res), cmp, "Mismatching matrix and petri net")

        def test_matrix2petrinet_orCross(self):
                # Fig. 2 in https://doi.org/10.1007/11494744_5
                I = {
                        "A": [],
                        "B": [],
                        "C": [{"A"}],
                        "D": [{"A","B"}]
                }
                O = {
                        "A": [{"C","D"}],
                        "B": [{"D"}],
                        "C": [],
                        "D": []
                }
                for t in I:
                        I[t] = [iset(s) for s in I[t]]
                        O[t] = [iset(s) for s in O[t]]
                res,_,_ = self._subject(I, O, T=I.keys())
#               self._visualise(res)
                cmp = """places: [ i, i('C', {'A'}), i('D', {'A', 'B'}), o, o('A', {'C', 'D'}), o('B', {'D'}) ]
transitions: [ (, None), (, None), (, None), (A, 'A'), (B, 'B'), (C, 'C'), (D, 'D') ]
arcs: [ (, None)->i('C', {'A'}), (, None)->i('D', {'A', 'B'}), (, None)->i('D', {'A', 'B'}), (A, 'A')->o('A', {'C', 'D'}), (B, 'B')->o('B', {'D'}), (C, 'C')->o, (D, 'D')->o, i('C', {'A'})->(C, 'C'), i('D', {'A', 'B'})->(D, 'D'), i->(A, 'A'), i->(B, 'B'), o('A', {'C', 'D'})->(, None), o('A', {'C', 'D'})->(, None), o('B', {'D'})->(, None) ]"""
                self.assertEqual(str(res), cmp, "Mismatching matrix and petri net")

        def test_matrix2petrinet_and(self):
                I = {
                        "A": [],
                        "B": [{"A"}],
                        "C": [{"A"}],
                        "D": [{"B"},{"C"}]
                }
                O = {
                        "A": [{"B"},{"C"}],
                        "B": [{"D"}],
                        "C": [{"D"}],
                        "D": []
                }
                for t in I:
                        I[t] = [iset(s) for s in I[t]]
                        O[t] = [iset(s) for s in O[t]]
                res,_,_ = self._subject(I, O, T=I.keys())
#               self._visualise(res)
                cmp = """places: [ ({'A'}, {'B'}), ({'A'}, {'C'}), ({'B'}, {'D'}), ({'C'}, {'D'}), i, o ]
transitions: [ (A, 'A'), (B, 'B'), (C, 'C'), (D, 'D') ]
arcs: [ (A, 'A')->({'A'}, {'B'}), (A, 'A')->({'A'}, {'C'}), (B, 'B')->({'B'}, {'D'}), (C, 'C')->({'C'}, {'D'}), (D, 'D')->o, ({'A'}, {'B'})->(B, 'B'), ({'A'}, {'C'})->(C, 'C'), ({'B'}, {'D'})->(D, 'D'), ({'C'}, {'D'})->(D, 'D'), i->(A, 'A') ]"""
                self.assertEqual(str(res), cmp, "Mismatching matrix and petri net")

        def test_matrix2petrinet_and2(self):
                I = {
                        "A": [],
                        "B": [],
                        "C": [{"A"},{"B"}],
                        "D": [{"A"},{"B"}]
                }
                O = {
                        "A": [{"C"},{"D"}],
                        "B": [{"C"},{"D"}],
                        "C": [],
                        "D": []
                }
                for t in I:
                        I[t] = [iset(s) for s in I[t]]
                        O[t] = [iset(s) for s in O[t]]
                res,_,_ = self._subject(I, O, T=I.keys())
#               self._visualise(res)
                cmp = """places: [ ({'A'}, {'C'}), ({'A'}, {'D'}), ({'B'}, {'C'}), ({'B'}, {'D'}), i, o ]
transitions: [ (A, 'A'), (B, 'B'), (C, 'C'), (D, 'D') ]
arcs: [ (A, 'A')->({'A'}, {'C'}), (A, 'A')->({'A'}, {'D'}), (B, 'B')->({'B'}, {'C'}), (B, 'B')->({'B'}, {'D'}), (C, 'C')->o, (D, 'D')->o, ({'A'}, {'C'})->(C, 'C'), ({'A'}, {'D'})->(D, 'D'), ({'B'}, {'C'})->(C, 'C'), ({'B'}, {'D'})->(D, 'D'), i->(A, 'A'), i->(B, 'B') ]"""
                self.assertEqual(str(res), cmp, "Mismatching matrix and petri net")

        def test_matrix2petrinet_full(self):
                # Fig. 3 in https://doi.org/10.1007/11494744_5
                I = {
                        "A": [],
                        "B": [{"A"}],
                        "C": [{"A"}],
                        "D": [{"A"}],
                        "E": [{"B"}, {"C"}],
                        "F": [{"B"}, {"D"}],
                        "G": [{"E"}, {"F"}]
                }
                O = {
                        "A": [{"B"}, {"C", "D"}],
                        "B": [{"E", "F"}],
                        "C": [{"E"}],
                        "D": [{"F"}],
                        "E": [{"G"}],
                        "F": [{"G"}],
                        "G": []
                }
                transitions = list(I.keys())
                res,_,_ = self._subject(I, O, T=transitions)
#               self._visualise(res, file="full.png")
                cmp = """places: [ ({'A'}, {'B'}), ({'A'}, {'C', 'D'}), ({'B'}, {'E', 'F'}), ({'C'}, {'E'}), ({'D'}, {'F'}), ({'E'}, {'G'}), ({'F'}, {'G'}), i, o ]
transitions: [ (A, 'A'), (B, 'B'), (C, 'C'), (D, 'D'), (E, 'E'), (F, 'F'), (G, 'G') ]
arcs: [ (A, 'A')->({'A'}, {'B'}), (A, 'A')->({'A'}, {'C', 'D'}), (B, 'B')->({'B'}, {'E', 'F'}), (C, 'C')->({'C'}, {'E'}), (D, 'D')->({'D'}, {'F'}), (E, 'E')->({'E'}, {'G'}), (F, 'F')->({'F'}, {'G'}), (G, 'G')->o, ({'A'}, {'B'})->(B, 'B'), ({'A'}, {'C', 'D'})->(C, 'C'), ({'A'}, {'C', 'D'})->(D, 'D'), ({'B'}, {'E', 'F'})->(E, 'E'), ({'B'}, {'E', 'F'})->(F, 'F'), ({'C'}, {'E'})->(E, 'E'), ({'D'}, {'F'})->(F, 'F'), ({'E'}, {'G'})->(G, 'G'), ({'F'}, {'G'})->(G, 'G'), i->(A, 'A') ]"""
                self.assertEqual(str(res), cmp, "Mismatching matrix and petri net")

        def test_matrix2petrinet_mixed(self):
                """Adapted from mining a random sample of BPI Challenge 2017, doi.org/10.4121/uuid:5f3067df-f10b-45da-b98b-86ae4c7a310b"""
                I = {
                        'A': [{'B', 'Y'}],
                        'B': [{'C'}],
                        'C': [{'Y'}],
                        'D': [{'Y'}],
                        'E': [{'F'}],
                        'F': [{'G'}],
                        'G': [{'H'}],
                        'H': [{'Y'}],
                        'I': [{'I'}],
                        'J': [{'I'}],
                        'K': [{'Z'}, {'S'}],
                        'L': [{'L'}],
                        'M': [{'L'}],
                        'N': [{'O'}],
                        'O': [{'L', 'X'}],
                        'P': [{'Q'}],
                        'Q': [{'X'}],
                        'R': [{'R', 'I'}],
                        'S': [{'R'}],
                        'T': [{'L', 'Y'}],
                        'U': [{'U'}, {'Y'}],
                        'V': [{'V', 'X'}],
                        'W': [{'L', 'W'}],
                        'X': [],
                        'Y': [],
                        'Z': [{'X'}]
                }
                O = {
                        'B': [{'A'}],
                        'Y': [{'A'}, {'D', 'T', 'U', 'C'}, {'H'}],
                        'C': [{'B'}],
                        'F': [{'E'}],
                        'G': [{'F'}],
                        'H': [{'G'}],
                        'I': [{'J', 'R'}, {'I'}],
                        'Z': [{'K'}],
                        'L': [{'M', 'O', 'T', 'L'}, {'W'}],
                        'O': [{'N'}],
                        'X': [{'O', 'Q', 'Z', 'V'}],
                        'Q': [{'P'}],
                        'R': [{'S'}, {'R'}],
                        'U': [{'U'}],
                        'V': [{'V'}],
                        'W': [{'W'}],
                        'P': [],
                        'N': [],
                        'T': [],
                        'M': [],
                        'D': [],
                        'A': [],
                        'E': [],
                        'K': [],
                        'S': [{'K'}],
                        'J': []
                }
                transitions = list(set(I.keys()) & set(O.keys()))
                res,_,_ = self._subject(I, O, T=transitions)
#               self._visualise(res)
                cmp = """places: [ ({'C'}, {'B'}), ({'F'}, {'E'}), ({'G'}, {'F'}), ({'H'}, {'G'}), ({'O'}, {'N'}), ({'Q'}, {'P'}), ({'S'}, {'K'}), ({'Z'}, {'K'}), i, i('A', {'B', 'Y'}), i('C', {'Y'}), i('D', {'Y'}), i('H', {'Y'}), i('I', {'I'}), i('J', {'I'}), i('L', {'L'}), i('M', {'L'}), i('O', {'L', 'X'}), i('Q', {'X'}), i('R', {'I', 'R'}), i('S', {'R'}), i('T', {'L', 'Y'}), i('U', {'U'}), i('U', {'Y'}), i('V', {'V', 'X'}), i('W', {'L', 'W'}), i('Z', {'X'}), o, o('B', {'A'}), o('I', {'I'}), o('I', {'J', 'R'}), o('L', {'L', 'M', 'O', 'T'}), o('L', {'W'}), o('R', {'R'}), o('R', {'S'}), o('U', {'U'}), o('V', {'V'}), o('W', {'W'}), o('X', {'O', 'Q', 'V', 'Z'}), o('Y', {'A'}), o('Y', {'C', 'D', 'T', 'U'}), o('Y', {'H'}) ]
transitions: [ (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (A, 'A'), (B, 'B'), (C, 'C'), (D, 'D'), (E, 'E'), (F, 'F'), (G, 'G'), (H, 'H'), (I, 'I'), (J, 'J'), (K, 'K'), (L, 'L'), (M, 'M'), (N, 'N'), (O, 'O'), (P, 'P'), (Q, 'Q'), (R, 'R'), (S, 'S'), (T, 'T'), (U, 'U'), (V, 'V'), (W, 'W'), (X, 'X'), (Y, 'Y'), (Z, 'Z') ]
arcs: [ (, None)->i('A', {'B', 'Y'}), (, None)->i('A', {'B', 'Y'}), (, None)->i('C', {'Y'}), (, None)->i('D', {'Y'}), (, None)->i('H', {'Y'}), (, None)->i('I', {'I'}), (, None)->i('J', {'I'}), (, None)->i('L', {'L'}), (, None)->i('M', {'L'}), (, None)->i('O', {'L', 'X'}), (, None)->i('O', {'L', 'X'}), (, None)->i('Q', {'X'}), (, None)->i('R', {'I', 'R'}), (, None)->i('R', {'I', 'R'}), (, None)->i('S', {'R'}), (, None)->i('T', {'L', 'Y'}), (, None)->i('T', {'L', 'Y'}), (, None)->i('U', {'U'}), (, None)->i('U', {'Y'}), (, None)->i('V', {'V', 'X'}), (, None)->i('V', {'V', 'X'}), (, None)->i('W', {'L', 'W'}), (, None)->i('W', {'L', 'W'}), (, None)->i('Z', {'X'}), (A, 'A')->o, (B, 'B')->o('B', {'A'}), (C, 'C')->({'C'}, {'B'}), (D, 'D')->o, (E, 'E')->o, (F, 'F')->({'F'}, {'E'}), (G, 'G')->({'G'}, {'F'}), (H, 'H')->({'H'}, {'G'}), (I, 'I')->o('I', {'I'}), (I, 'I')->o('I', {'J', 'R'}), (J, 'J')->o, (K, 'K')->o, (L, 'L')->o('L', {'L', 'M', 'O', 'T'}), (L, 'L')->o('L', {'W'}), (M, 'M')->o, (N, 'N')->o, (O, 'O')->({'O'}, {'N'}), (P, 'P')->o, (Q, 'Q')->({'Q'}, {'P'}), (R, 'R')->o('R', {'R'}), (R, 'R')->o('R', {'S'}), (S, 'S')->({'S'}, {'K'}), (T, 'T')->o, (U, 'U')->o, (U, 'U')->o('U', {'U'}), (V, 'V')->o, (V, 'V')->o('V', {'V'}), (W, 'W')->o, (W, 'W')->o('W', {'W'}), (X, 'X')->o('X', {'O', 'Q', 'V', 'Z'}), (Y, 'Y')->o('Y', {'A'}), (Y, 'Y')->o('Y', {'C', 'D', 'T', 'U'}), (Y, 'Y')->o('Y', {'H'}), (Z, 'Z')->({'Z'}, {'K'}), ({'C'}, {'B'})->(B, 'B'), ({'F'}, {'E'})->(E, 'E'), ({'G'}, {'F'})->(F, 'F'), ({'H'}, {'G'})->(G, 'G'), ({'O'}, {'N'})->(N, 'N'), ({'Q'}, {'P'})->(P, 'P'), ({'S'}, {'K'})->(K, 'K'), ({'Z'}, {'K'})->(K, 'K'), i('A', {'B', 'Y'})->(A, 'A'), i('C', {'Y'})->(C, 'C'), i('D', {'Y'})->(D, 'D'), i('H', {'Y'})->(H, 'H'), i('I', {'I'})->(I, 'I'), i('J', {'I'})->(J, 'J'), i('L', {'L'})->(L, 'L'), i('M', {'L'})->(M, 'M'), i('O', {'L', 'X'})->(O, 'O'), i('Q', {'X'})->(Q, 'Q'), i('R', {'I', 'R'})->(R, 'R'), i('S', {'R'})->(S, 'S'), i('T', {'L', 'Y'})->(T, 'T'), i('U', {'U'})->(U, 'U'), i('U', {'Y'})->(U, 'U'), i('V', {'V', 'X'})->(V, 'V'), i('W', {'L', 'W'})->(W, 'W'), i('Z', {'X'})->(Z, 'Z'), i->(I, 'I'), i->(L, 'L'), i->(X, 'X'), i->(Y, 'Y'), o('B', {'A'})->(, None), o('I', {'I'})->(, None), o('I', {'J', 'R'})->(, None), o('I', {'J', 'R'})->(, None), o('L', {'L', 'M', 'O', 'T'})->(, None), o('L', {'L', 'M', 'O', 'T'})->(, None), o('L', {'L', 'M', 'O', 'T'})->(, None), o('L', {'L', 'M', 'O', 'T'})->(, None), o('L', {'W'})->(, None), o('R', {'R'})->(, None), o('R', {'S'})->(, None), o('U', {'U'})->(, None), o('V', {'V'})->(, None), o('W', {'W'})->(, None), o('X', {'O', 'Q', 'V', 'Z'})->(, None), o('X', {'O', 'Q', 'V', 'Z'})->(, None), o('X', {'O', 'Q', 'V', 'Z'})->(, None), o('X', {'O', 'Q', 'V', 'Z'})->(, None), o('Y', {'A'})->(, None), o('Y', {'C', 'D', 'T', 'U'})->(, None), o('Y', {'C', 'D', 'T', 'U'})->(, None), o('Y', {'C', 'D', 'T', 'U'})->(, None), o('Y', {'C', 'D', 'T', 'U'})->(, None), o('Y', {'H'})->(, None) ]"""
                self.assertEqual(str(res), cmp, "Mismatching matrix and petri net")

        def test_matrix2petrinet_mixed2(self):
                """Adapted from mining a random sample of BPI Challenge 2017, doi.org/10.4121/uuid:5f3067df-f10b-45da-b98b-86ae4c7a310b"""
                I = {
                        'A': [{'B'}, {'C'}],
                        'B': [{'Y'}],
                        'C': [{'C'}],
                        'D': [{'E'}, {'C'}],
                        'E': [{'F'}],
                        'F': [{'G'}],
                        'G': [{'N'}, {'H'}],
                        'H': [{'C'}],
                        'I': [{'W', 'I', 'K'}],
                        'J': [{'I'}],
                        'K': [{'X'}, {'K'}],
                        'L': [{'M', 'K'}],
                        'M': [{'K'}],
                        'N': [{'P', 'N'}],
                        'O': [{'N'}],
                        'P': [{'Q'}],
                        'Q': [{'K'}],
                        'R': [{'S'}],
                        'S': [{'K'}],
                        'T': [{'T'}, {'I'}],
                        'U': [{'T'}],
                        'V': [{'C'}],
                        'W': [{'W'}],
                        'X': [{'X'}],
                        'Y': [],
                        'Z': [{'E'}]
                }
                O = {
                        'B': [{'A'}],
                        'C': [{'D', 'A', 'H', 'V'}, {'C'}],
                        'Y': [{'B'}],
                        'E': [{'D', 'Z'}],
                        'F': [{'E'}],
                        'G': [{'F'}],
                        'H': [{'G'}],
                        'I': [{'J', 'I'}, {'T'}],
                        'K': [{'L'}, {'Q', 'S', 'M', 'I', 'K'}],
                        'M': [{'L'}],
                        'N': [{'O', 'N'}, {'G'}],
                        'Q': [{'P'}],
                        'S': [{'R'}],
                        'T': [{'T'}, {'U'}],
                        'W': [{'I'}, {'W'}],
                        'X': [{'X', 'K'}],
                        'A': [],
                        'D': [],
                        'V': [],
                        'L': [],
                        'P': [{'N'}],
                        'R': [],
                        'U': [],
                        'J': [],
                        'O': [],
                        'Z': []
                }
                transitions = list(set(I.keys()) & set(O.keys()))
                res,_,_ = self._subject(I, O, T=transitions)
#               self._visualise(res)
                cmp = """places: [ ({'B'}, {'A'}), ({'C'}, {'A', 'D', 'H', 'V'}), ({'C'}, {'C'}), ({'E'}, {'D', 'Z'}), ({'F'}, {'E'}), ({'G'}, {'F'}), ({'Q'}, {'P'}), ({'S'}, {'R'}), ({'Y'}, {'B'}), i, i('G', {'H'}), i('G', {'N'}), i('I', {'I', 'K', 'W'}), i('J', {'I'}), i('K', {'K'}), i('K', {'X'}), i('L', {'K', 'M'}), i('M', {'K'}), i('N', {'N', 'P'}), i('O', {'N'}), i('Q', {'K'}), i('S', {'K'}), i('T', {'I'}), i('T', {'T'}), i('U', {'T'}), i('W', {'W'}), i('X', {'X'}), o, o('H', {'G'}), o('I', {'I', 'J'}), o('I', {'T'}), o('K', {'I', 'K', 'M', 'Q', 'S'}), o('K', {'L'}), o('M', {'L'}), o('N', {'G'}), o('N', {'N', 'O'}), o('P', {'N'}), o('T', {'T'}), o('T', {'U'}), o('W', {'I'}), o('W', {'W'}), o('X', {'K', 'X'}) ]
transitions: [ (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (, None), (A, 'A'), (B, 'B'), (C, 'C'), (D, 'D'), (E, 'E'), (F, 'F'), (G, 'G'), (H, 'H'), (I, 'I'), (J, 'J'), (K, 'K'), (L, 'L'), (M, 'M'), (N, 'N'), (O, 'O'), (P, 'P'), (Q, 'Q'), (R, 'R'), (S, 'S'), (T, 'T'), (U, 'U'), (V, 'V'), (W, 'W'), (X, 'X'), (Y, 'Y'), (Z, 'Z') ]
arcs: [ (, None)->i('G', {'H'}), (, None)->i('G', {'N'}), (, None)->i('I', {'I', 'K', 'W'}), (, None)->i('I', {'I', 'K', 'W'}), (, None)->i('I', {'I', 'K', 'W'}), (, None)->i('J', {'I'}), (, None)->i('K', {'K'}), (, None)->i('K', {'X'}), (, None)->i('L', {'K', 'M'}), (, None)->i('L', {'K', 'M'}), (, None)->i('M', {'K'}), (, None)->i('N', {'N', 'P'}), (, None)->i('N', {'N', 'P'}), (, None)->i('O', {'N'}), (, None)->i('Q', {'K'}), (, None)->i('S', {'K'}), (, None)->i('T', {'I'}), (, None)->i('T', {'T'}), (, None)->i('U', {'T'}), (, None)->i('W', {'W'}), (, None)->i('X', {'X'}), (A, 'A')->o, (B, 'B')->({'B'}, {'A'}), (C, 'C')->({'C'}, {'A', 'D', 'H', 'V'}), (C, 'C')->({'C'}, {'C'}), (D, 'D')->o, (E, 'E')->({'E'}, {'D', 'Z'}), (F, 'F')->({'F'}, {'E'}), (G, 'G')->({'G'}, {'F'}), (H, 'H')->o('H', {'G'}), (I, 'I')->o('I', {'I', 'J'}), (I, 'I')->o('I', {'T'}), (J, 'J')->o, (K, 'K')->o('K', {'I', 'K', 'M', 'Q', 'S'}), (K, 'K')->o('K', {'L'}), (L, 'L')->o, (M, 'M')->o('M', {'L'}), (N, 'N')->o('N', {'G'}), (N, 'N')->o('N', {'N', 'O'}), (O, 'O')->o, (P, 'P')->o('P', {'N'}), (Q, 'Q')->({'Q'}, {'P'}), (R, 'R')->o, (S, 'S')->({'S'}, {'R'}), (T, 'T')->o('T', {'T'}), (T, 'T')->o('T', {'U'}), (U, 'U')->o, (V, 'V')->o, (W, 'W')->o('W', {'I'}), (W, 'W')->o('W', {'W'}), (X, 'X')->o('X', {'K', 'X'}), (Y, 'Y')->({'Y'}, {'B'}), (Z, 'Z')->o, ({'B'}, {'A'})->(A, 'A'), ({'C'}, {'A', 'D', 'H', 'V'})->(A, 'A'), ({'C'}, {'A', 'D', 'H', 'V'})->(D, 'D'), ({'C'}, {'A', 'D', 'H', 'V'})->(H, 'H'), ({'C'}, {'A', 'D', 'H', 'V'})->(V, 'V'), ({'C'}, {'C'})->(C, 'C'), ({'E'}, {'D', 'Z'})->(D, 'D'), ({'E'}, {'D', 'Z'})->(Z, 'Z'), ({'F'}, {'E'})->(E, 'E'), ({'G'}, {'F'})->(F, 'F'), ({'Q'}, {'P'})->(P, 'P'), ({'S'}, {'R'})->(R, 'R'), ({'Y'}, {'B'})->(B, 'B'), i('G', {'H'})->(G, 'G'), i('G', {'N'})->(G, 'G'), i('I', {'I', 'K', 'W'})->(I, 'I'), i('J', {'I'})->(J, 'J'), i('K', {'K'})->(K, 'K'), i('K', {'X'})->(K, 'K'), i('L', {'K', 'M'})->(L, 'L'), i('M', {'K'})->(M, 'M'), i('N', {'N', 'P'})->(N, 'N'), i('O', {'N'})->(O, 'O'), i('Q', {'K'})->(Q, 'Q'), i('S', {'K'})->(S, 'S'), i('T', {'I'})->(T, 'T'), i('T', {'T'})->(T, 'T'), i('U', {'T'})->(U, 'U'), i('W', {'W'})->(W, 'W'), i('X', {'X'})->(X, 'X'), i->(C, 'C'), i->(W, 'W'), i->(X, 'X'), i->(Y, 'Y'), o('H', {'G'})->(, None), o('I', {'I', 'J'})->(, None), o('I', {'I', 'J'})->(, None), o('I', {'T'})->(, None), o('K', {'I', 'K', 'M', 'Q', 'S'})->(, None), o('K', {'I', 'K', 'M', 'Q', 'S'})->(, None), o('K', {'I', 'K', 'M', 'Q', 'S'})->(, None), o('K', {'I', 'K', 'M', 'Q', 'S'})->(, None), o('K', {'I', 'K', 'M', 'Q', 'S'})->(, None), o('K', {'L'})->(, None), o('M', {'L'})->(, None), o('N', {'G'})->(, None), o('N', {'N', 'O'})->(, None), o('N', {'N', 'O'})->(, None), o('P', {'N'})->(, None), o('T', {'T'})->(, None), o('T', {'U'})->(, None), o('W', {'I'})->(, None), o('W', {'W'})->(, None), o('X', {'K', 'X'})->(, None), o('X', {'K', 'X'})->(, None) ]"""
                self.assertEqual(str(res), cmp, "Mismatching matrix and petri net")

        @staticmethod
        def _subject(I, O, T):
                # convert to indexable sets
                for t in T:
                        I[t] = [iset(s) for s in I[t]]
                        O[t] = [iset(s) for s in O[t]]
                return matrix2petrinet(GeneticMatrix(I, O, T))

        @staticmethod
        def _visualise(model, init = None, final = None, file = "test.png"):
                save_vis_petri_net(
                        model,
                        init or utils.initial_marking.discover_initial_marking(model),
                        final or utils.final_marking.discover_final_marking(model),
                        file_path = file,
                        debug = True
                )

if __name__ == '__main__':
        unittest.main()
