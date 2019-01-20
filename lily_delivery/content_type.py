
import mimetypes


def get_content_type(path):

    content_type, _ = mimetypes.guess_type(path, strict=True)

    if content_type is None and path.endswith('.woff2'):
        content_type = 'font/woff2'

    return content_type
