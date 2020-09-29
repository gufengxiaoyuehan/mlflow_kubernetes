import os

from setuptools import setup, find_packages

with open('README.rst') as f:
    long_description = f.read()


def package_files(directory):
    paths = []
    for (path, _, filenames) in os.walk(directory):
        for filename in filenames:
            paths.append(os.path.join("..", path, filename))
    return paths


setup(
    name='mlflow-kubernetes',
    version='0.1.0',
    author='logan',
    description='mlflow model auto-deploy to kubernetes and SaaS',
    long_description=long_description,
    url='http://codeup.teambition.com/',
    packages=find_packages(),
    package_data={"": package_files("mlflow_kubernetes/deployments/dockerfile")},
    zip_safe=False,
    install_requires=[
        'kubernetes',
        'requests',
        'pandas',
        'click',
    ],
    extras_require={
        'server': [
            'docker',
            'redis',
            'gitpython',
            'mlflow@git+ssh://git@codeup.teambition.com/fusiontree/fusionplatform/mlflow.git@dev#egg=mlflow',
        ]
    },
    entry_points={
        "console_scripts": "mlflowkube=mlflow_kubernetes.cli:cli"
    },
)