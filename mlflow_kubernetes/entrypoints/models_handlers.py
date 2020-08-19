from mlflow_kubernetes.deployments.kubernetes import KubernetesDeployment

class ModelCreateHandler:
    """
    todo(login):
    """
    def __init__(self, kube_deployment: KubernetesDeployment):
        self.kube_deployment = kube_deployment

    def handle(self, event):
        self.kube_deployment.create_deployment(event.name, event.model_uri)
