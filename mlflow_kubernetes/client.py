"""
invoke mlflow deployed in kubernetes clusts through construct a ``ModelService`` instance.
"""
import pandas
import requests
from kubernetes import config as kube_config, client

# not import variables directly, as we expects users will change them
from . import config


def _df_to_dict(df: pandas.DataFrame):
    data = dict(columns=df.columns.to_list())
    data['data'] = df.values.tolist()
    return data


class ModelService:
    """
    kubernetes service client provide inference from input dataframe
    """

    def __init__(self, model_name, kube_config_path=None):
        kube_config.load_kube_config(config_file=kube_config_path)
        kube_cluster_info = client.Configuration()
        self._request = requests.Session()
        self._request.headers.update("Authorization", f"Bearer {config.KUBE_AUTH_TOKEN}")
        self.model_name = model_name
        # TODO(logan): use nodeport type in production. docker-kube not expose port in cluster
        self._kube_service_proxiy_uri = f'{kube_cluster_info.host}/api/v1/namespaces/{config.KUBE_MLLFOW_MODELS_NAMESPACE}' \
                                        f'/services/{model_name}/proxy/invocations'

    def predict(self, df):
        """
        method input/output interface like :py:meth:`mlflow.pyfunc.PyFuncModel.predict
        :param df: dict of dataframe
        :return: a pandas dataframe
        """
        if isinstance(df, pandas.DataFrame):
            body = _df_to_dict(df)
        else:
            body = df
        resp = self._request.post(self._kube_service_proxiy_uri, json=body)
        if not resp.status_code == 200:
            resp.raise_for_status()
        return resp.json()