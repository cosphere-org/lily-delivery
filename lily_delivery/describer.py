
from contextlib import contextmanager

import click


class Describer:

    @contextmanager
    def header(self, text):
        text = text.upper()
        click.secho(f'\n\n[START] {text}', fg='blue')  # noqa
        yield
        click.secho(f'[STOP] {text}', fg='blue')  # noqa

    @contextmanager
    def subheader(self, text):
        click.secho(f'\n\n[START] {text}', fg='green')  # noqa
        yield
        click.secho(f'[STOP] {text}', fg='green')  # noqa

    @contextmanager
    def text(self, text):
        click.secho(text, fg='white')
        yield
