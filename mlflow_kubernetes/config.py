import os

# constant and environment variable

# kuberenetes
KUBERNETES_CONFIG_PATH = os.environ.get('KUBERNETES_CONFIG_PATH', None)
# expose port for each pod
KUBE_DEFAULT_SERVICE_PORT = 8080
# model's namespace
KUBE_MLLFOW_MODELS_NAMESPACE = 'default'

# mlflow model image listen port
MLFLOW_MODEL_DEFAULT_TARGET_PORT = 8080

# client access token
KUBE_AUTH_TOKEN = os.environ.get("KUBE_AUTH_TOKEN", None)

# base image path used build mlflow model image
MLFLOW_MODEL_BASE_IMAGE_PATH = os.path.join(os.path.dirname(__file__), 'deployments', 'dockerfile')
MLFLOW_MODEL_BASE_IMAGE_DOCKERFILE = 'mlflow.dockerfile'

# mlflow models published uri
MODELS_EVENT_URI = os.environ.get('MODELS_EVENT_URI', None)