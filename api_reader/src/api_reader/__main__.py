"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Api_Reader."""


if __name__ == "__main__":
    main(prog_name="api_reader")  # pragma: no cover
