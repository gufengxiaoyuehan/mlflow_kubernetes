import re

from kubernetes import client
from kubernetes import config as kube_config
from kubernetes.client.rest import ApiException
from mlflow.exceptions import MlflowException

from mlflow_kubernetes import logger
# not import variables directly, as we expects users will change them
from mlflow_kubernetes import config
from mlflow_kubernetes.deployments.model_registry import DockerModelImageRegistry, docker_registry_info_from_env

canonical_name_pattern = re.compile(r"[a-zA-Z0-9\-.]+")


class KubernetesDeployment():
    def __init__(self, target_uri, kube_config_path=None) -> None:
        super().__init__(target_uri)
        kube_config.load_kube_config(config_file=kube_config_path)
        self._core_api = client.CoreV1Api()
        self._apps_api = client.AppsV1Api()

    def create_deployment(self, name, model_uri, flavor=None, config=None):
        """
        create a combination of kubernetes service, deployment that provide
        predict service for specified flavor model

        :param name: Unique name to use for deployment. If another deployment exists with the same
                     name, raises a :py:class:`mlflow.exceptions.MlflowException`
        :param model_uri: URI of model to deploy
        :param flavor: (optional) Model flavor to deploy. If unspecified, a default flavor
                       will be chosen.
        :param config: (optional) Dict containing updated target-specific configuration for the
                       deployment
        :return: Dict corresponding to created deployment, which must contain the 'name' key.
        """
        if not canonical_name_pattern.match(name):
            canonical_name = re.sub(r"[^a-zA-Z0-9\-.]", '', name)
            logger.logger.warn('deployment name {} not validated by kubernetes, covert to {}'.format(
                name, canonical_name
            ))
        else:
            canonical_name = name

        if self.get_deployment(canonical_name):
            raise MlflowException('service {} already exists'.format(canonical_name))
        registry_info = docker_registry_info_from_env()
        docker_registry = DockerModelImageRegistry(canonical_name, registry_info)
        docker_registry.create_image_from_uri(model_uri)
        self.create_kube_deployment_with_service(canonical_name, docker_registry.image_name)

    def get_deployment(self, name):
        try:
            return self._apps_api.read_namespaced_deployment(name=name, namespace=config.KUBE_MLLFOW_MODELS_NAMESPACE)
        except client.rest.ApiException as e:
            if e.status == 404:
                return None
            raise

    def create_deployment_object(self, name, image_tag):
        # Configureate Pod template container
        container = client.V1Container(
            name=name,
            image=image_tag,
            ports=[client.V1ContainerPort(container_port=config.MLFLOW_MODEL_DEFAULT_TARGET_PORT, name=name)],
            resources=client.V1ResourceRequirements(
                requests={"cpu": "100m", "memory": "200Mi"},
                limits={"cpu": "500m", "memory": "500Mi"}
            )
        )
        # Create and configurate a spec section
        # !! need create a secret with type docker-registry contains private registry credential
        secret = client.V1LocalObjectReference(name='regcred')
        template = client.V1PodTemplateSpec(
            metadata=client.V1ObjectMeta(labels={"name": name}),
            spec=client.V1PodSpec(
                containers=[container], image_pull_secrets=[secret],
            ),
        )
        # Create the specification of deployment
        spec = client.V1DeploymentSpec(
            replicas=1,
            template=template,
            selector={'matchLabels': {'name': name}})
        # Instantiate the deployment object
        deployment = client.V1Deployment(
            api_version="apps/v1",
            kind="Deployment",
            metadata=client.V1ObjectMeta(name=name),
            spec=spec)

        return deployment

    def create_kube_deployment_with_service(self, name, image):
        deployment_obj = self.create_deployment_object(name=name, image_tag=image)
        logger.logger.info('create deployment:%s', deployment_obj)
        deployment_response = self._apps_api.create_namespaced_deployment(
            body=deployment_obj,
            namespace=config.KUBE_MLLFOW_MODELS_NAMESPACE
        )
        service_response = self.create_kube_service(name)
        return deployment_response, service_response

    def create_kube_service(self, name):
        service = client.V1Service()
        service.api_version = "v1"
        service.kind = "Service"
        service.metadata = client.V1ObjectMeta(name=name)
        spec = client.V1ServiceSpec()
        spec.type = 'NodePort'
        spec.selector = {"name": name}
        spec.ports = [client.V1ServicePort(protocol="TCP", port=config.KUBE_DEFAULT_SERVICE_PORT, target_port=name)]
        service.spec = spec
        return self._core_api.create_namespaced_service(namespace=config.KUBE_MLLFOW_MODELS_NAMESPACE, body=service)

    def delete_deployment(self, name):
        try:
            self._apps_api.delete_namespaced_deployment(
                name=name, namespace=config.KUBE_MLLFOW_MODELS_NAMESPACE,
                body=client.V1DeleteOptions(propagation_policy="Foreground", grace_period_seconds=5)
            )
        except client.rest.ApiException as e:
            if e.status != 404:
                raise

        try:
            self._core_api.delete_namespaced_service(
                name=name, namespace=config.KUBE_MLLFOW_MODELS_NAMESPACE
            )
        except client.rest.ApiException as e:
            if e.status != 404:
                raise

    def list_deployments(self):
        return self._apps_api.list_namespaced_deployment(namespace=config.KUBE_MLLFOW_MODELS_NAMESPACE)

    def update_deployment(self, name, model_uri, flavor, config):
        # TODO(logan): need implementation
        raise NotImplementedError('update not supported now')
