import click
import mlflow_kubernetes.deployments.cli

@click.group()
@click.version_option()
def cli():
    pass


cli.add_command(mlflow_kubernetes.deployments.cli)


if __name__ == '__main__':
    cli()
