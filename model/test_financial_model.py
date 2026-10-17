import unittest

import financial_model as fm


class ModelSanity(unittest.TestCase):
    def test_contribution_is_price_net_of_refunds_and_variable_costs(self):
        s = fm.SCENARIOS[1]
        expected = s.price_per_file * (1 - s.refund_writeoff_rate) - s.variable_cost_per_file
        self.assertAlmostEqual(s.contribution_per_file, expected)
        self.assertLess(s.variable_cost_per_file, 0.06 * s.price_per_file + 1)

    def test_backsolve_hits_target_and_is_minimal(self):
        for s in fm.SCENARIOS:
            b = fm.backsolve(s)
            self.assertGreaterEqual(b["operating_profit_before_founder_pay"], fm.TARGET - 1)
            smaller = fm.month_economics(s, b["active_agents"] * 0.97, b["active_agents"] * 0.97 * s.agent_monthly_churn)
            self.assertLess(smaller["operating_profit_before_founder_pay"], fm.TARGET)

    def test_profit_identity(self):
        r = fm.month_economics(fm.SCENARIOS[1], 50, 5)
        rebuilt = (r["revenue"] - r["refunds_writeoffs"] - r["variable_costs"] - r["fixed_costs"]
                   - r["acquisition_cash"] - r["outsourced_delivery"])
        self.assertAlmostEqual(rebuilt, r["operating_profit_before_founder_pay"])

    def test_ramp_converges_to_ceiling(self):
        s = fm.SCENARIOS[1]
        rows = fm.ramp(s, months=400)
        self.assertAlmostEqual(rows[-1]["active_agents"], fm.steady_state_ceiling(s), places=3)

    def test_binomial_tail(self):
        self.assertAlmostEqual(fm.binom_tail(40, 0.1, 0), 1.0)
        self.assertAlmostEqual(fm.binom_tail(10, 0.5, 10), 0.5 ** 10)


if __name__ == "__main__":
    unittest.main()
