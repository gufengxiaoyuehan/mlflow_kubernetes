import subprocess
from collections import namedtuple
import os
import os
import tempfile
from collections import namedtuple
import git
import docker
import docker.errors
from mlflow.models.flavor_backend_registry import get_flavor_backend
from mlflow.models.model import MLMODEL_FILE_NAME, Model
from mlflow.store.artifact.models_artifact_repo import ModelsArtifactRepository
from mlflow.tracking.artifact_utils import _download_artifact_from_uri
from mlflow.utils.uri import append_to_uri_path

from mlflow_kubernetes import config
from mlflow_kubernetes.logger import logger

RegistryInfo = namedtuple('RegistryInfo', 'username password registry namespace')

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))
IMAGE_BASE = "mlflow-base"

CODEUP_FORKED_MLFLOW = 'git+ssh://codeup.teambition.com/fusiontree/fusionplatform/mlflow'
CODEUP_FORKED_MLFLOW_BRANCH = 'dev'


def docker_registry_info_from_env():
    """docker registry info used to push and pull images, 
    
    author info:
    username, password. 
    
    regsitry info:

    registry: registry image save to, like **registry.cn-hangzhou.aliyuncs.com**
    namespace image belongs to, default to username
    """
    username = os.environ["DOCKER_USERNAME"]
    password = os.environ["DOCKER_PASSWORD"]
    registry_uri = os.environ.get('DOCKER_REGISTRY_URI')
    namespace = os.environ.get('DOCKER_NAMESPACE') or username
    return RegistryInfo(username, password, registry_uri, namespace)


def _generate_normal_name_for_repositry(image_name, registry_info):
    """
    convert image_name to a legal name for specified registry
    :param image_name: name that not conform to registry rules
    :param registry_info: registry information about remote registry
    :return: noramlized name
    """
    prefix = '{registory_host}/{namespace}'.format(registory_host=registry_info.registry,
                                                   namespace=registry_info.namespace)
    if not image_name.startswith(prefix):
        image_name = '{}/{}'.format(prefix, image_name)
    return image_name


def _install_image_base_if_not_exists(client: docker.DockerClient, image_name):
    try:
        client.images.get(name=image_name)
    except docker.errors.ImageNotFound:
        logger.debug('base image "mlflow-base" not exists, build it')
        client.images.build(path=config.MLFLOW_MODEL_BASE_IMAGE_PATH,
                            dockerfile=config.MLFLOW_MODEL_BASE_IMAGE_DOCKERFILE )


class DockerModelImageRegistry:
    """
    create a image from mlflow model uri,
    sync it model with docker registry.
    """

    def __init__(self, image_name, registry_info: RegistryInfo):
        """

        :param image_name:
        :param registry_info:
        """
        self.registry_info = registry_info
        self._client = None
        self._image_name = image_name
        self._base_image = IMAGE_BASE

    @property
    def image_name(self):
        """canonical image name """
        return _generate_normal_name_for_repositry(self._image_name, self.registry_info)

    @property
    def client(self) -> docker.DockerClient:
        if self._client is None:
            self._client = docker.from_env()
            self._client.login(
                username=self.registry_info.username,
                password=self.registry_info.password,
                registry=self.registry_info.registry
            )
        return self._client

    def create_image_from_uri(self, uri, **kwargs):
        """
        build and push image from uri to registry
        :return:
        """
        _install_image_base_if_not_exists(self.client, image_name=self._base_image)
        self.build_image_local_from_model_uri(uri, self._base_image, **kwargs)
        self.push_image_to_repository()

    def build_image_local_from_model_uri(self, model_uri, base_image, **kwargs):
        """build PythonModel Backed service image from model_uri

        :param base_image: image base from which  build  model image
        :param model_uri: directory contains pyfunc model filesystem.
                          <"pyfunc-filename-system"
                          https://mlflow.org/docs/latest/python_api/mlflow.pyfunc.html#pyfunc-filename-system>_
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            if ModelsArtifactRepository.is_models_uri(model_uri):
                underlying_model_uri = ModelsArtifactRepository.get_underlying_uri(model_uri)
            else:
                underlying_model_uri = model_uri

            local_path = _download_artifact_from_uri(
                append_to_uri_path(underlying_model_uri, MLMODEL_FILE_NAME), output_path=tmp_dir
            )

            model_meta = Model.load(local_path)

            flavor_name, flavor_backend = get_flavor_backend(model_meta, **kwargs)
            if flavor_name is None:
                raise TypeError("no suitable backend was found for the model")

            if not flavor_backend.can_build_image():
                raise AttributeError('flavor {} not support build image'.format(flavor_name))

            mlflow_clone_path = os.path.join(tmp_dir, 'mlflow')
            logger.info("clone mlflow from codeup %s@%s to %s", CODEUP_FORKED_MLFLOW,
                        CODEUP_FORKED_MLFLOW_BRANCH, mlflow_clone_path)

            git.Repo.clone_from(
                CODEUP_FORKED_MLFLOW, mlflow_clone_path,
                single_branch=True, branch=CODEUP_FORKED_MLFLOW_BRANCH
            )
            return flavor_backend.build_image(
                model_uri, self.image_name,
                mlflow_home=mlflow_clone_path, base_image=base_image
            )

    def push_image_to_repository(self):
        """push image to registry. used docker local settings
        """
        logger.info("=== pushing docker image %s =========", self.image_name)
        for line in self.client.images.push(self.image_name, stream=True, decode=True):
            if 'error' in line and line['error']:
                raise RuntimeError('error while pushing to docker registry "{}"'.format(line['error']))
            else:
                logger.info(line)

        return self.client.images.get_registry_data(self.image_name).id
