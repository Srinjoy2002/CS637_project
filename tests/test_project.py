"""Curated-project regression checks; run python -m unittest discover -s tests."""
import hashlib
import itertools
import json
from pathlib import Path
import unittest

import numpy as np
from attack.detector_diagnostics import Config, diagnose, run_counts
from attack.exhaustive import optimize
from models.paper import get_model
from simulation.closed_loop import simulate

ROOT = Path(__file__).resolve().parents[1]


class ProjectTests(unittest.TestCase):
    def test_author_sources_unchanged(self):
        for name, digest in json.loads((ROOT / 'docs/vendor_sha256.json').read_text()).items():
            self.assertEqual(hashlib.sha256((ROOT / 'vendor/REP_v1.2' / name).read_bytes()).hexdigest(), digest)

    def test_all_twenty_policy_replays(self):
        from tools.ppt_evidence import replay_cases
        self.assertEqual(len(replay_cases()), 10)

    def test_plant_evolves_and_memory_policy_matches(self):
        for name in ('furuta_hold', 'furuta_zero', 'qt_nmp', 'qt_zero'):
            m = get_model(name)
            x = simulate(m, [0, 1, 1, 0, 1, 0])
            for k, bit in enumerate([0, 1, 1, 0, 1, 0]):
                np.testing.assert_allclose(x[k+1, :m.nplant], m.A @ x[k, :m.nplant] + m.B @ x[k, -m.ninput:], atol=1e-13)
                if bit:
                    np.testing.assert_array_equal(x[k+1, m.nplant:-m.ninput], x[k, m.nplant:-m.ninput])
                    expected = x[k, -m.ninput:] if name in ('furuta_hold', 'qt_nmp') else np.zeros(m.ninput)
                    np.testing.assert_array_equal(x[k+1, -m.ninput:], expected)

    def test_tank_output_cost_scaling(self):
        m = get_model('qt_nmp')
        x = simulate(m, [0, 1, 0])
        y = m.output(x)
        np.testing.assert_allclose(np.sum(y*y, axis=1), np.einsum('bi,ij,bj->b', x, m.Q_output, x))
        np.testing.assert_array_equal(m.Q_output, m.Q_rep / 4)

    def test_run_count_patterns(self):
        for ell in range(1, 8):
            for bits in itertools.product([0, 1], repeat=ell):
                z = [0] + list(bits) + [0]
                expected = [sum(z[i] == 0 and z[i+k+1] == 0 and all(z[i+1:i+k+1])
                                for i in range(len(z)-k-1)) for k in range(5)]
                self.assertEqual(run_counts(z, 4).tolist(), expected)

    def test_example_statistic_and_threshold(self):
        d = diagnose([0, 1, 1, 0, 1, 0, 0], Config(window=20, amax=3, detector='bin_chi2'))
        self.assertAlmostEqual(d['chi_square'], 19/3)
        self.assertEqual(d['N'], 3)
        self.assertTrue(d['accepted'])

    def test_pruned_search_matches_bruteforce(self):
        for detector in ('bin', 'chi2', 'bin_chi2'):
            cfg = Config(window=4, p=.17, alpha=.05, amax=2, detector=detector)
            for name in ('furuta_hold', 'furuta_zero', 'qt_nmp'):
                m = get_model(name)
                costs = []
                for bits in itertools.product([0, 1], repeat=6):
                    z = [0] + list(bits) + [0]
                    if diagnose(z, cfg)['accepted']:
                        x = simulate(m, z)
                        costs.append(float(x[-2] @ m.Q_rep @ x[-2]))
                self.assertAlmostEqual(optimize(name, 6, cfg)['attack_rep'], max(costs), places=12)


if __name__ == '__main__':
    unittest.main()
