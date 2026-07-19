"""Tests for recognizing timetable table structure."""

import pandas as pd

from emeris_timetable.pdf_reader import is_section_header, is_timeslot_row


def test_is_section_header_recognizes_supported_headings():
    assert is_section_header(pd.Series(["Academic Week 3", "Monday"]))
    assert is_section_header(pd.Series(["ASSESS WEEK", "Monday"]))
    assert not is_section_header(pd.Series(["09H00 - 10H00", "COMP1234"]))


def test_is_timeslot_row_accepts_both_time_formats():
    assert is_timeslot_row(pd.Series(["9H00 - 10H00", "COMP1234 Room101"]))
    assert is_timeslot_row(pd.Series(["09:00 - 10:00", "COMP1234 Room101"]))
    assert not is_timeslot_row(pd.Series(["Academic Week 3", "Monday"]))
