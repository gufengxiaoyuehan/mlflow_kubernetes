"""
invoke mlflow deployed in kubernetes clusts through construct a ``ModelService`` instance.
"""
from itertools import product

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

    def __init__(self, model_name, version, kube_config_path=None):
        kube_config.load_kube_config(config_file=kube_config_path)
        self._request = requests.Session()
        self.model_name = f"{model_name}-{version}"
        self._kube = client.CoreV1Api()
        # host port used to access model service running in kubernetes
        self._host_port_pairs = set()

    def get_service_host_port(self):
        name = self.model_name
        app = self._kube
        hosts = [
            container.status.host_ip
            for container in app.list_namespaced_pod(
                namespace=config.KUBE_MLLFOW_MODELS_NAMESPACE, label_selector=f"name={name}"
            ).items
            if container.status.phase == 'Running'
        ]

        ports = [
            port.node_port
            for port in app.read_namespaced_service(
                name=name, namespace=config.KUBE_MLLFOW_MODELS_NAMESPACE
            ).spec.ports
        ]

        return set(product(hosts, ports))

    def predict(self, df: pandas.DataFrame) -> pandas.DataFrame:
        """
        method input/output interface like :py:meth:`mlflow.pyfunc.PyFuncModel.predict
        :param df: dict of dataframe
        :return: a pandas dataframe
        """
        if isinstance(df, pandas.DataFrame):
            body = _df_to_dict(df)
        else:
            body = df

        if not self._host_port_pairs:
            self._host_port_pairs = self.get_service_host_port()

        invalidate_idx = set()
        resp = None
        for host, port in self._host_port_pairs:
            try:
                resp = self._request.post(f'http://{host}:{port}/invocations', json=body)
            except requests.exceptions.ConnectionError:
                invalidate_idx.add((host, port))
                continue
            else:
                break

        self._host_port_pairs -= invalidate_idx
        # none of these request success connected
        if resp is None:
            raise ConnectionError(
                'connection failed to all services: {}'.format(','.join(
                    ['%s:%s' % (host, port) for host, port in invalidate_idx]
                )))

        if resp.status_code != 200:
            raise ValueError(resp.json())

        return pandas.DataFrame(resp.json())
