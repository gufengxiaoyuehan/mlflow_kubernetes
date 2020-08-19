import pytest
from mock import MagicMock
import pandas

from mlflow_kubernetes import ModelService

@pytest.fixture()
def magic_mock():
    return MagicMock()

def test_model_predict_df(magic_mock):
    model_service = ModelService(model_name='fake')
    model_service._request = magic_mock

    df = pandas.DataFrame(columns=['a', 'b', 'c'], data=[[1,2,3], [3,4,5]])

    result = model_service.predict(df)

    assert model_service._request.assert_called_once()