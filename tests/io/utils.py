from datetime import datetime

import pytest

from psdm_analysis.io.utils import check_filter


def test_check_filter_both_dates_provided_valid():
    filter_start = datetime(2022, 1, 1)
    filter_end = datetime(2022, 1, 31)
    check_filter(filter_start, filter_end)  # Should not raise any exception


def test_check_filter_both_dates_none():
    check_filter(None, None)  # Should not raise any exception


def test_check_filter_only_start_date_provided():
    filter_start = datetime(2022, 1, 1)
    with pytest.raises(
        ValueError,
        match="Both start and end of the filter must be provided if one is provided.",
    ):
        check_filter(filter_start, None)


def test_check_filter_only_end_date_provided():
    filter_end = datetime(2022, 1, 31)
    with pytest.raises(
        ValueError,
        match="Both start and end of the filter must be provided if one is provided.",
    ):
        check_filter(None, filter_end)


def test_check_filter_start_date_after_end_date():
    filter_start = datetime(2022, 1, 31)
    filter_end = datetime(2022, 1, 1)
    with pytest.raises(ValueError, match="Filter start must be before end."):
        check_filter(filter_start, filter_end)