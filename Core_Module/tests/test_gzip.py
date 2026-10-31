import gzip

from django.test import TestCase


class GZipMiddlewareTests(TestCase):
    def test_html_response_is_compressed(self):
        response = self.client.get('/', HTTP_ACCEPT_ENCODING='gzip')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Encoding'], 'gzip')
        body = b''.join(response.streaming_content) if response.streaming else response.content
        self.assertGreater(len(body), 0)
        html = gzip.decompress(body).decode('utf-8')
        self.assertIn('</html>', html)

    def test_plain_request_is_not_compressed(self):
        response = self.client.get('/', HTTP_ACCEPT_ENCODING='identity')

        self.assertEqual(response.status_code, 200)
        self.assertNotIn('gzip', response.get('Content-Encoding', ''))
