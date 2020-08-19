from mlflow_kubernetes.deployments import model_registry
import pytest

registry_info = model_registry.RegistryInfo(
    'fake', 'fake', 'localhost', 'fake'
)


@pytest.fixture()
def magic_registry(magic_mock):
    registry = model_registry.DockerModelImageRegistry('fake', registry_info)
    registry._client = magic_mock
    return registry


def test_build_image_from_uri(created_model, magic_registry):
    magic_registry.create_image_from_uri(f'models:/{created_model}/1')
    # TO MUCH PATCH test make no sense

