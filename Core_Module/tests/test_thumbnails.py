import tempfile
from pathlib import Path

from django.test import SimpleTestCase, override_settings
from PIL import Image

from Core_Module.thumbnails import thumb_path, thumb_url


class ImageStub:
    """Minimal stand-in for a FileField bound to a real file on disk."""

    def __init__(self, path, name):
        self.path = str(path)
        self.name = name
        self.url = '/media/' + name


class ThumbnailTests(SimpleTestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.media_root = Path(self.tmp.name)
        self.source = self.media_root / 'products' / 'sample.jpg'
        self.source.parent.mkdir(parents=True)
        Image.new('RGB', (1200, 1500), (200, 120, 90)).save(self.source, 'JPEG', quality=92)
        self.image = ImageStub(self.source, 'products/sample.jpg')

    def _override(self):
        return override_settings(MEDIA_ROOT=str(self.media_root), MEDIA_URL='/media/')

    def test_generates_webp_with_requested_width(self):
        with self._override():
            path = thumb_path(self.image, 480)

            self.assertIsNotNone(path)
            self.assertTrue(path.is_file())
            self.assertEqual(path.suffix, '.webp')
            self.assertTrue(thumb_url(self.image, 480).startswith('/media/thumbs/'))
            with Image.open(path) as out:
                self.assertEqual(out.format, 'WEBP')
                self.assertEqual(out.width, 480)

    def test_second_call_reuses_cached_file(self):
        with self._override():
            first = thumb_path(self.image, 208)
            stamp = first.stat().st_mtime_ns
            second = thumb_path(self.image, 208)

            self.assertEqual(first, second)
            self.assertEqual(second.stat().st_mtime_ns, stamp)

    def test_changed_source_produces_new_url(self):
        with self._override():
            first = thumb_url(self.image, 96)
            self.source.touch()
            self.assertNotEqual(first, thumb_url(self.image, 96))

    def test_missing_source_falls_back_to_original_url(self):
        missing = ImageStub(self.media_root / 'products' / 'missing.jpg', 'products/missing.jpg')

        with self._override():
            self.assertIsNone(thumb_path(missing, 480))
            self.assertEqual(thumb_url(missing, 480), missing.url)

    def test_empty_field_returns_empty_url(self):
        with self._override():
            self.assertEqual(thumb_url(None, 480), '')
