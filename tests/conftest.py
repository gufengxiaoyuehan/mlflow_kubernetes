import logging
import signal
import os
from subprocess import PIPE
import sys
from tempfile import TemporaryFile
import tempfile
import pytest
import subprocess
import shlex
from pathlib import Path

@pytest.fixture(scope='session')
def mlflow_server():
    with tempfile.TemporaryDirectory() as tmpdir:
        proc = start_server(tmpdir)
        yield tmpdir
        pgrp = os.getpgid(proc.pid)
        os.killpg(pgrp, signal.SIGINT)
        return proc.wait()


def start_server(tmpdir):
    sqlite_path = Path(tmpdir) / 'mlflow.sqlite'
    artifact_path = Path(tmpdir) / 'mlruns'
    if not artifact_path.exists():
        artifact_path.mkdir()
    cmd = '{} -m mlflow.cli server --backend-store-uri sqlite:///{} --default-artifact-root {} '.format(
        sys.executable, sqlite_path, artifact_path.absolute()
        )
    proc = subprocess.Popen( 
       cmd,
       cwd=tmpdir, stdout=PIPE, stderr=subprocess.STDOUT,shell=True,
       text=True, preexec_fn= os.setsid 
    )
    while 1:
        ln = proc.stdout.readline()
        print(ln)
        if 'Booting worker with pid' in ln :
            break
        if proc.poll():
            raise RuntimeError(proc.returncode)

    return proc


def build_mlflow_model(homedir):
    from sklearn import datasets
    from sklearn.ensemble import RandomForestClassifier
    import mlflow
    import mlflow.sklearn
    from mlflow.models.signature import infer_signature
    import pandas as pd
    from mlflow.tracking._model_registry import fluent

    mlflow.set_tracking_uri('http://localhost:5000')
    with mlflow.start_run() as run:
        iris = datasets.load_iris()
        iris_train = pd.DataFrame(iris.data, columns=iris.feature_names)
        clf = RandomForestClassifier(max_depth=7, random_state=0)
        clf.fit(iris_train, iris.target)
        signature = infer_signature(iris_train, clf.predict(iris_train))
        model_name = "iris_rf"
        mlflow.sklearn.log_model(clf, model_name, signature=signature, registered_model_name=model_name)
        logging.info('runs:', os.fwalk(homedir))
        return fluent.MlflowClient().get_model_version_download_uri(name=model_name, version=1)
    
@pytest.fixture(scope='session')
def created_model(mlflow_server):
    homedir = mlflow_server
    name = build_mlflow_model(homedir)
    return name
    

if __name__ == "__main__":
    import pathlib
    proc = start_server(pathlib.Path('.'))
    proc.send_signal(1)