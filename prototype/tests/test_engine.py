"""AC1 (deadline arithmetic) and AC2 (validation)."""

import datetime as dt
import unittest

from c2c.engine import BusinessCalendar, DealError, compute_schedule
from c2c.holidays_us import federal_holidays

from helpers import example_profile, minimal_deal, one_rule_profile, sample_deal

D = dt.date.fromisoformat


def single(effective, closing="2027-06-30", **rule):
    schedule = compute_schedule(minimal_deal(effective, closing, n=rule.pop("n", 0)),
                                one_rule_profile(days={"term": "n"}, **rule))
    return schedule.deadlines[0]


class HandComputedCases(unittest.TestCase):
    """The eight cases from ACCEPTANCE.md, AC1."""

    def test_1_calendar_no_roll(self):
        self.assertEqual(single("2026-10-16", n=7).date, D("2026-10-23"))

    def test_2_calendar_roll_forward_over_weekend(self):
        self.assertEqual(single("2026-10-22", n=3, roll="forward").date, D("2026-10-26"))

    def test_3_business_days_skip_thanksgiving(self):
        self.assertEqual(single("2026-11-24", n=3, count="business").date, D("2026-11-30"))

    def test_4_roll_forward_over_christmas(self):
        self.assertEqual(single("2026-12-15", n=10, roll="forward").date, D("2026-12-28"))

    def test_5_observed_independence_day_rolls_forward(self):
        cal = BusinessCalendar()
        self.assertFalse(cal.is_business_day(D("2026-07-03")))
        self.assertEqual(cal.roll(D("2026-07-03"), "forward"), D("2026-07-06"))

    def test_6_before_closing_roll_backward(self):
        deal = minimal_deal("2026-11-01", "2026-11-30")
        profile = one_rule_profile(anchor="closing_date", days={"fixed": 1}, direction="before", roll="backward")
        self.assertEqual(compute_schedule(deal, profile).deadlines[0].date, D("2026-11-27"))

    def test_7_observed_new_year_on_previous_dec_31(self):
        self.assertEqual(single("2027-12-30", closing="2028-02-01", n=1, count="business").date, D("2028-01-03"))

    def test_8_chained_anchor(self):
        profile = one_rule_profile(days={"fixed": 7})
        profile["deadlines"].append({"key": "b", "label": "B", "anchor": "d", "owner": "seller",
                                     "days": {"fixed": 2}, "count": "business"})
        sched = compute_schedule(minimal_deal("2026-10-16", "2026-12-01"), profile)
        by_key = {d.key: d.date for d in sched.deadlines}
        self.assertEqual(by_key["d"], D("2026-10-23"))
        self.assertEqual(by_key["b"], D("2026-10-27"))


class Explanations(unittest.TestCase):
    def test_explanation_shows_arithmetic_and_roll(self):
        d = single("2026-10-22", n=3, roll="forward")
        self.assertIn("+ 3 calendar days", d.explanation)
        self.assertIn("rolled forward to Mon Oct 26, 2026", d.explanation)

    def test_non_rolling_weekend_is_flagged_in_explanation_and_warnings(self):
        d = single("2026-10-14", n=10)  # Sat Oct 24
        self.assertIn("does NOT roll", d.explanation)
        self.assertTrue(any("does not roll" in w for w in d.warnings))

    def test_zero_offset_reads_as_written(self):
        deal = minimal_deal("2026-11-01", "2026-11-30")
        d = compute_schedule(deal, one_rule_profile(anchor="closing_date")).deadlines[0]
        self.assertEqual(d.explanation, "closing date as written: Mon Nov 30, 2026")

    def test_due_time_and_timezone(self):
        d = single("2026-10-16", n=7, due_time="17:00")
        self.assertEqual(d.due.isoformat(), "2026-10-23T17:00:00-05:00")


class HolidayCrossCheck(unittest.TestCase):
    """Compare our generator with an independent implementation (PyPI `holidays`)."""

    def test_matches_holidays_package_2025_2030(self):
        try:
            import holidays
        except ImportError:
            self.skipTest("holidays package not installed")
        for year in range(2025, 2031):
            ours = set(federal_holidays(year))
            theirs = set(holidays.country_holidays("US", years=[year - 1, year, year + 1], observed=True))
            # The package lists only observed dates for weekend holidays; ours also
            # keeps the actual (weekend) date, which is a non-business day anyway.
            weekday_ours = {d for d in ours if d.weekday() < 5}
            weekday_theirs = {d for d in theirs if d.year == year and d.weekday() < 5}
            self.assertEqual(weekday_ours, weekday_theirs, f"mismatch in {year}")


class Validation(unittest.TestCase):
    def assert_error(self, deal, profile, fragment):
        with self.assertRaises(DealError) as ctx:
            compute_schedule(deal, profile)
        self.assertTrue(any(fragment in e for e in ctx.exception.errors),
                        f"'{fragment}' not in {ctx.exception.errors}")

    def test_closing_before_effective(self):
        self.assert_error(minimal_deal("2026-10-20", "2026-10-01"), one_rule_profile(), "before effective_date")

    def test_negative_days_names_field(self):
        deal = sample_deal()
        deal["terms"]["inspection_days"] = -2
        self.assert_error(deal, example_profile(), "terms.inspection_days")

    def test_non_integer_days(self):
        deal = sample_deal()
        deal["terms"]["inspection_days"] = "ten"
        self.assert_error(deal, example_profile(), "terms.inspection_days")

    def test_missing_required_term_names_term(self):
        deal = sample_deal()
        del deal["terms"]["earnest_money_days"]
        self.assert_error(deal, example_profile(), "terms.earnest_money_days")

    def test_missing_optional_term_is_skipped_not_error(self):
        deal = sample_deal()
        del deal["terms"]["appraisal_days"]
        sched = compute_schedule(deal, example_profile())
        self.assertNotIn("appraisal", {d.key for d in sched.deadlines})
        self.assertTrue(any("Appraisal" in s for s in sched.skipped))

    def test_skipped_optional_anchor_skips_dependent(self):
        deal = sample_deal()
        profile = example_profile()
        for rule in profile["deadlines"]:
            if rule["key"] == "inspection_end":
                rule["optional"] = True
        del deal["terms"]["inspection_days"]
        sched = compute_schedule(deal, profile)
        self.assertNotIn("inspection_response", {d.key for d in sched.deadlines})

    def test_bad_date(self):
        self.assert_error(minimal_deal("2026-13-01", "2026-12-01"), one_rule_profile(), "effective_date")

    def test_unknown_anchor(self):
        self.assert_error(minimal_deal("2026-10-01", "2026-12-01"), one_rule_profile(anchor="nope"), "anchor 'nope'")

    def test_bad_timezone(self):
        deal = minimal_deal("2026-10-01", "2026-12-01")
        deal["timezone"] = "Mars/Olympus"
        self.assert_error(deal, one_rule_profile(), "timezone")

    def test_deadline_after_closing_is_warning(self):
        sched = compute_schedule(minimal_deal("2026-10-01", "2026-10-10", n=20),
                                 one_rule_profile(days={"term": "n"}))
        self.assertTrue(any("after closing" in w for w in sched.warnings))

    def test_profile_direction_typo_is_error(self):
        self.assert_error(minimal_deal("2026-10-01", "2026-12-01"), one_rule_profile(direction="befor"), "direction")

    def test_before_closing_non_rolling_weekend_warns(self):
        deal = minimal_deal("2026-11-01", "2026-11-30")  # Mon closing; -2 days = Sat
        profile = one_rule_profile(anchor="closing_date", days={"fixed": 2}, direction="before")
        self.assertTrue(any("does not roll" in w for w in compute_schedule(deal, profile).warnings))

    def test_weekend_closing_is_warning(self):
        sched = compute_schedule(minimal_deal("2026-10-01", "2026-10-31"), one_rule_profile())
        self.assertTrue(any("not a business day" in w for w in sched.warnings))

    def test_sample_deal_schedule(self):
        sched = compute_schedule(sample_deal(), example_profile())
        got = {d.key: d.date.isoformat() for d in sched.deadlines}
        self.assertEqual(got, {
            "earnest_money": "2026-10-19",       # Sat 10-17 rolled forward
            "inspection_end": "2026-10-24",      # Sat, no roll (flagged)
            "inspection_response": "2026-10-27", # 2 business days after Sat 10-24
            "title_review": "2026-10-29",
            "appraisal": "2026-11-04",
            "financing": "2026-11-09",           # Sun 11-08 rolled forward
            "insurance": "2026-11-13",
            "walkthrough": "2026-11-19",
            "closing": "2026-11-20",
        })
        dues = [d.due for d in sched.deadlines]
        self.assertEqual(dues, sorted(dues))
        self.assertEqual(len(sched.warnings), 1)
        self.assertIn("Inspection period ends", sched.warnings[0])


if __name__ == "__main__":
    unittest.main()
