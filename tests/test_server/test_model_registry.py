import docker.errors
from unittest import mock
from mlflow_kubernetes.deployments.model_registry import _install_image_base_if_not_exists


class DockerFaker:
    def __init__(self):
        self.images = DockerImageFaker()


class DockerImageFaker:
    def __init__(self):
        self.get = mock.Mock()
        self.build = mock.Mock()


def test_base_image_install_if_not_exists():
    docker_client = DockerFaker()
    docker_client.images.get.side_effect = docker.errors.ImageNotFound('fake')

    _install_image_base_if_not_exists(docker_client, 'fake')

    docker_client.images.get.assert_called_with(name='fake')
    docker_client.images.build.assert_called_once()




