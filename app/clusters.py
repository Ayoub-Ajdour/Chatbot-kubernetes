import os
from kubernetes import client, config
import logging # <-- THE MISSING IMPORT

KUBE_CONFIG_PATH = os.environ.get("CHATBOT_KUBECONFIG_PATH")

class ClusterManager:
    def __init__(self):
        self.clusters = {}
        self.current_context = None
        self.load_clusters()

    def load_clusters(self):
        """Load available kubeconfig contexts from the explicit path."""
        if not KUBE_CONFIG_PATH or not os.path.exists(KUBE_CONFIG_PATH):
            logging.error(f"ClusterManager: Kubeconfig path not found. Var value: {KUBE_CONFIG_PATH}")
            self.clusters = {}
            return
        
        try:
            contexts, _ = config.list_kube_config_contexts(config_file=KUBE_CONFIG_PATH)
            for context in contexts:
                context_name = context['name']
                self.clusters[context_name] = context
            logging.info(f"Successfully loaded clusters: {list(self.clusters.keys())}")
        except Exception as e:
            logging.error(f"Error loading clusters from {KUBE_CONFIG_PATH}: {e}")
            self.clusters = {}

    def set_cluster(self, cluster_name):
        """Set the active cluster context using the explicit path."""
        if cluster_name in self.clusters:
            self.current_context = cluster_name
            try:
                config.load_kube_config(config_file=KUBE_CONFIG_PATH, context=cluster_name)
                logging.info(f"Set active Kubernetes context to: {cluster_name}")
                return True
            except Exception as e:
                logging.error(f"Error setting cluster context '{cluster_name}': {e}")
                return False
        return False

    def get_current_cluster(self):
        """Return the current cluster context."""
        return self.current_context or "default"

    def list_clusters(self):
        """Return list of available clusters."""
        return list(self.clusters.keys())

cluster_manager = ClusterManager()
