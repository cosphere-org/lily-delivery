
import pytest

from lily_delivery.content_type import get_content_type


@pytest.mark.parametrize(
    'path,expected',
    [
        # -- case 0: png font
        ('something/new/1.png', 'image/png'),

        # -- case 1: html font
        ('something/better/index.14.5.html', 'text/html'),

        # -- case 2: js font
        ('something/better/main-48394893.js', 'application/javascript'),

        # -- case 3: woff2 font
        ('something/better/shiny.woff2', 'font/woff2'),

    ])
def test_get_content_type(path, expected):

    assert get_content_type(path) == expected
