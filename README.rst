mlflow-kubernetes
==================

``mlflow-kubernetes`` will publish mlflow models to on-premise kubernetes clusters automatically when
there are new models registered or old models changed in mlflow_, so others can use these models as SaaS.
this models contains two related but independent sub-modules, ``server`` and ``client``.
one for listen events about models to create/update/delete pods in kubernetes, the other can used to access
these models to get predicted value.

.. _mlflow: https://codeup.teambition.com/fusiontree/fusionplatform/mlflow

installation
-------------

you can install it from pypi, by default only client dependent package installed,
if you want build an new server add *[server]* right after package name:

.. caution:: you need forked mlflow_ access privilege when startup a listening server.

or install from source code:

.. code-block:: bash

    pip install git+ssh://git@codeup.teambition.com/fusiontree/...#egg=mlflow-kubernetes


usage
-------
this models contains server module to deploy models and client models to retrieve inference
by invoking models already published.

configuration
^^^^^^^^^^^^^^
configuration can expose by environment variables and through ``config`` module.

**kubernetes**

``KUBERNETES_CONFIG_PATH`` :

  config file provided access and authorization information to communicate with kubernetes.
  both server and client needs access kubernetes through webserver api, by defualt use system contained
  .

**docker**

    not provide now, assumption of all configuration runing this module had been set properly

**message bus**

``MODELS_EVENT_URI``:

    event message bus server listen for. current support redis pubsub as a target uri. like
    ``redis://localhost:6379``





server
^^^^^^^
make sure you install required ``server``  extras by

.. code-block:: bash

    pip install git+ssh://git@codeup.teambition.com/fusiontree/...#egg=mlflow-kubernetes[server]

then start up a server, by default it will try to scribe a redis pubsub and assume local configuration
can access the kubernetes cluster overwrite by environment variable or input parameters.

for example::

    mlflowkube models server --model-events-uri redis://host:port \
      --kubernetes-config-path ~/path/to/kubernetes/config


client
^^^^^^^
access models in ``mlflow-kubernetes`` is easy, just build a  new ``ModelService``:

.. code-block:: python

    from mlflow_kubernetes import ModelService
    from mlflow_kubernetes import config
    import pandas as pd
    from sklearn import datasets
    # set KUBE_AUTH_TOKEN in environment variable also works
    config.KUBE_AUTH_TOKEN = '***kubernetes webapi access token***'
    model_service = ModelService(model_name='iris-rf')
    iris = datasets.load_iris()
    iris_train = pd.DataFrame(iris.data, columns=iris.feature_names)
    result = model_service.predict(iris_train)

