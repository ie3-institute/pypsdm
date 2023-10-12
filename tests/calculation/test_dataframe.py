import pandas as pd

from pypsdm.processing.dataframe import divide_positive_negative

index = pd.date_range("2012-01-01 10:00:00", "2012-01-01 13:00:00", freq="h")
data = [1, 2, -2, 3]
df = pd.DataFrame(index=index, data={"p": data, "q": data.copy()})


def test_divide_positive_negative():
    positive, negative = divide_positive_negative(df)
    assert len(positive) == 4
    assert len(negative) == 4
    assert positive.p.sum() == 6
    assert positive.q.sum() == 6
    assert negative.p.sum() == -2
    assert negative.q.sum() == -2
