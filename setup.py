from setuptools import setup

with open('README.rst') as f:
    long_description = f.read()

setup(
    name='mlflow-kubernetes',
    version='0.1.0',
    author='logan',
    description='mlflow model auto-deploy to kubernetes and SaaS',
    long_description=long_description,
    url='http://codeup.teambition.com/',
    packages=['mlflow_kubernetes',],
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