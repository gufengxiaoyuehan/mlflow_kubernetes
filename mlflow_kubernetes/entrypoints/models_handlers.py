from mlflow_kubernetes.deployments.kubernetes import KubernetesDeployment

class ModelCreateHandler:
    """
    todo(login):
    """
    topics = ['model_created']

    def __init__(self, kube_deployment: KubernetesDeployment):
        self.kube_deployment = kube_deployment

    def handle_model_created(self, event):
        model_info = event['model']
        model_name = model_info['name']
        model_version = model_info['version']
        model_uri = model_info['source']
        self.kube_deployment.create_deployment(model_name, model_version, model_uri)

    def handle(self, topic, event):
        return getattr(self, 'handle_' +  topic)(event)
