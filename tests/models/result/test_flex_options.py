def test_from_csv(gwr):
    flex_options_results = gwr.results.participants.flex
    assert len(flex_options_results) == 1
