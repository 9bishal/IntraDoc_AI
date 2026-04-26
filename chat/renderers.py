"""
Custom renderers for chat endpoints.
"""

from rest_framework.renderers import BaseRenderer


class NDJSONRenderer(BaseRenderer):
    """
    Renderer placeholder for newline-delimited JSON streaming responses.

    ChatView returns a StreamingHttpResponse directly, but DRF still performs
    content negotiation first. Registering this renderer allows requests with
    `Accept: application/x-ndjson` to pass negotiation.
    """

    media_type = 'application/x-ndjson'
    format = 'ndjson'
    charset = 'utf-8'
    render_style = 'binary'

    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return b''
        if isinstance(data, (bytes, bytearray)):
            return bytes(data)
        if isinstance(data, str):
            return data.encode(self.charset)
        return str(data).encode(self.charset)
