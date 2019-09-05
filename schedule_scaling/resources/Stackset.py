import abc
from pykube.objects import NamespacedAPIObject

class Scalable(abc.ABC):

    @abc.abstractmethod
    def set_replicas(self, count: int):
        pass

    @abc.abstractmethod
    def get_replicas(self):
        pass

class StackSet(NamespacedAPIObject, Scalable):
    """
    Use latest workloads API version (apps/v1), pykube is stuck with old version
    """

    version = "zalando.org/v1"
    endpoint = "stacksets"
    kind = "StackSet"

    def set_replicas(self, count):
        self.obj['spec']['stackTemplate']['spec']['replicas'] = count

    def get_replicas(self):
        return int(self.obj['spec']['stackTemplate']['spec']['replicas'])

    def has_hpa(self):
        return 'horizontalPodAutoscaler' in self.obj['spec']['stackTemplate']['spec']

    def get_min_replicas(self):
        return self.obj['spec']['stackTemplate']['spec']['horizontalPodAutoscaler']['minReplicas']

    def set_min_replicas(self, min_replicas):
        self.obj['spec']['stackTemplate']['spec']['horizontalPodAutoscaler']['minReplicas'] = min_replicas

    def get_max_replicas(self):
        return self.obj['spec']['stackTemplate']['spec']['horizontalPodAutoscaler']['maxReplicas']

    def set_max_replicas(self, max_replicas):
        self.obj['spec']['stackTemplate']['spec']['horizontalPodAutoscaler']['maxReplicas'] = max_replicas

    def save_state(self):
        self.annotations[DOWNSCALER_SAVED_ANNOTATION] = json.dumps(
            self.obj['spec']['stackTemplate']['spec']['horizontalPodAutoscaler'])
        self.obj['spec']['stackTemplate']['spec']['horizontalPodAutoscaler'] = None
