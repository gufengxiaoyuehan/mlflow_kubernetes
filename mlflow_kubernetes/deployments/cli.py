import urllib.parse

import click
from .. import config
from .kubernetes import KubernetesDeployment
from mlflow_kubernetes.entrypoints.messagebus import RedisMessageBus
from mlflow_kubernetes.entrypoints.models_handlers import ModelCreateHandler

@click.group('models', help="listen for mlflow model event")
def commands():
    """
    run server to lister
    :return:
    """


@commands.command("server")
@click.option("--models-event-target", 'event_target', default=None,
                 help="model event message bus identifier, currently support redis"
                      ", like redis://localhost:7369/0"
)
@click.option('--kubernetes-config-path', default=None)
def server(event_target, kubernetes_config_path):
    """
    run server to listen for incoming models, create or update models changes corresponding
    """
    kubernetes_config_path = kubernetes_config_path or config.KUBERNETES_CONFIG_PATH
    kube = KubernetesDeployment('kubernetes', kubernetes_config_path)

    handler = ModelCreateHandler(kube)

    target_uri = event_target or config.MODELS_EVENT_URI
    event_target_scheme = urllib.parse.urlparse(target_uri)
    if event_target_scheme.scheme != 'redis':
        raise ValueError('scheme %s not support currently', event_target_scheme.scheme)

    host, *port = event_target_scheme.netloc.split(':')
    port = int(port[0]) if port else None

    message_bus = RedisMessageBus(event_target_scheme.host, port, handler)
    message_bus.run()


@commands.command("predict")
@click.option("--model", "model", require=True, help="model name")
@click.option('--input-path', '-i', default=None, help="input data")
@click.option('--output-path', '-o', default=None, help="output data")
def predict(model):
    """
    invoke service named by *model*, and return data
    :param model:
    :return:
    """