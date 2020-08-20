import click
import mlflow_kubernetes.entrypoints.cli

@click.group()
@click.version_option()
def cli():
    pass


cli.add_command(mlflow_kubernetes.entrypoints.cli.commands)


if __name__ == '__main__':
    cli()
