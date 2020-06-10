from pykube import Deployment
import pykube

# extends pykube.Deployment, overriding version "v1beta1" with "apps/v1"
class CADeployment(pykube.Deployment):

    version = "apps/v1"
