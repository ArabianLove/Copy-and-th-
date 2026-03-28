import struct
import pytest
from src.forensic_metadata import (
    parse_youtube_url,
    analyze_video_id,
    categorize_charset,
    calculate_shannon_entropy,
    generate_derived_urls,
    extract_page_metadata,
    analyze_image_bytes,
    detect_image_format,
    detect_appended_data,
    calculate_byte_entropy,
    extract_readable_strings,
    detect_exif_markers,
)


# --- Test URL Parsing ---

class TestParseYoutubeUrl:
    def test_youtube_music_url(self):
        url = "https://music.youtube.com/watch?v=4wHDzicDp3E&feature=shared"
        result = parse_youtube_url(url)
        assert result["video_id"] == "4wHDzicDp3E"
        assert result["piattaforma"] == "youtube_music"
        assert result["parametri"]["feature"] == "shared"

    def test_standard_youtube_url(self):
        result = parse_youtube_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        assert result["video_id"] == "dQw4w9WgXcQ"
        assert result["piattaforma"] == "youtube"

    def test_short_url(self):
        result = parse_youtube_url("https://youtu.be/dQw4w9WgXcQ")
        assert result["video_id"] == "dQw4w9WgXcQ"

    def test_embed_url(self):
        result = parse_youtube_url("https://www.youtube.com/embed/dQw4w9WgXcQ")
        assert result["video_id"] == "dQw4w9WgXcQ"

    def test_non_youtube_url(self):
        result = parse_youtube_url("https://example.com/page")
        assert result["video_id"] is None
        assert result["piattaforma"] == "unknown"


# --- Test Video ID Analysis ---

class TestAnalyzeVideoId:
    def test_valid_id(self):
        result = analyze_video_id("4wHDzicDp3E")
        assert result["formato_valido"] is True
        assert result["lunghezza"] == 11
        assert result["entropia_shannon"] > 0
        assert result["hash_sha256"] is not None
        assert "base64_decoded_hex" in result

    def test_charset_analysis(self):
        result = analyze_video_id("4wHDzicDp3E")
        charset = result["charset_usato"]
        assert charset["cifre"] > 0
        assert charset["maiuscole"] > 0
        assert charset["minuscole"] > 0


class TestCategorizeCharset:
    def test_mixed(self):
        result = categorize_charset("AbC123_-")
        assert result["maiuscole"] == 2
        assert result["minuscole"] == 1
        assert result["cifre"] == 3
        assert result["speciali"] == 2


class TestShannonEntropy:
    def test_zero_entropy(self):
        assert calculate_shannon_entropy("aaaa") == 0.0

    def test_max_entropy_binary(self):
        assert calculate_shannon_entropy("ab") == 1.0

    def test_empty(self):
        assert calculate_shannon_entropy("") == 0.0


class TestGenerateDerivedUrls:
    def test_all_urls_present(self):
        urls = generate_derived_urls("4wHDzicDp3E")
        assert "4wHDzicDp3E" in urls["watch_url"]
        assert "4wHDzicDp3E" in urls["music_url"]
        assert "4wHDzicDp3E" in urls["embed_url"]
        assert "4wHDzicDp3E" in urls["thumbnail_hq"]
        assert "4wHDzicDp3E" in urls["oembed_json"]
        assert len(urls) >= 15


# --- Test HTML Metadata Extraction ---

class TestExtractPageMetadata:
    def test_og_tags(self):
        html = """
        <html><head>
        <title>Test Video</title>
        <meta property="og:title" content="My Video">
        <meta property="og:type" content="video">
        <meta property="og:image" content="https://img.example.com/thumb.jpg">
        <meta name="twitter:card" content="player">
        <meta itemprop="name" content="Video Name">
        </head><body></body></html>
        """
        result = extract_page_metadata(html)
        assert result["title"] == "Test Video"
        assert result["open_graph"]["og:title"] == "My Video"
        assert result["twitter_cards"]["twitter:card"] == "player"
        assert result["itemprop"]["name"] == "Video Name"

    def test_json_ld(self):
        html = """
        <html><head>
        <script type="application/ld+json">
        {"@type": "VideoObject", "name": "Test"}
        </script>
        </head><body></body></html>
        """
        result = extract_page_metadata(html)
        assert len(result["json_ld"]) == 1
        assert result["json_ld"][0]["@type"] == "VideoObject"

    def test_empty_html(self):
        result = extract_page_metadata("")
        assert result["title"] is None
        assert result["open_graph"] == {}


# --- Test Image Forensics ---

class TestDetectImageFormat:
    def test_jpeg(self):
        assert detect_image_format(b'\xff\xd8\xff\xe0' + b'\x00' * 100) == "JPEG"

    def test_png(self):
        assert detect_image_format(b'\x89PNG\r\n\x1a\n' + b'\x00' * 100) == "PNG"

    def test_gif(self):
        assert detect_image_format(b'GIF89a' + b'\x00' * 100) == "GIF89a"

    def test_unknown(self):
        assert detect_image_format(b'\x00\x00\x00\x00') == "sconosciuto"


class TestDetectAppendedData:
    def test_clean_jpeg(self):
        data = b'\xff\xd8\xff\xe0' + b'\x00' * 50 + b'\xff\xd9'
        result = detect_appended_data(data)
        assert result["trovati"] is False

    def test_jpeg_with_appended_data(self):
        data = b'\xff\xd8\xff\xe0' + b'\x00' * 50 + b'\xff\xd9' + b'HIDDEN_DATA'
        result = detect_appended_data(data)
        assert result["trovati"] is True
        assert result["bytes_extra"] == len(b'HIDDEN_DATA')

    def test_non_jpeg(self):
        result = detect_appended_data(b'\x00\x00\x00\x00')
        assert result["trovati"] is False


class TestByteEntropy:
    def test_uniform(self):
        data = bytes(range(256)) * 100
        entropy = calculate_byte_entropy(data)
        assert entropy == 8.0  # Max entropy for byte data

    def test_low_entropy(self):
        data = b'\x00' * 1000
        assert calculate_byte_entropy(data) == 0.0


class TestExtractReadableStrings:
    def test_finds_strings(self):
        data = b'\x00\x00' + b'HelloWorld123' + b'\x00\x00'
        result = extract_readable_strings(data, min_length=8)
        assert "HelloWorld123" in result

    def test_ignores_short(self):
        data = b'\x00' + b'Hi' + b'\x00'
        result = extract_readable_strings(data, min_length=8)
        assert len(result) == 0


class TestDetectExifMarkers:
    def test_jpeg_with_app1(self):
        # Minimal JPEG with APP1 segment
        app1_data = b'\x00' * 10
        app1_segment = b'\xff\xe1' + struct.pack(">H", len(app1_data) + 2) + app1_data
        data = b'\xff\xd8' + app1_segment + b'\xff\xd9'
        result = detect_exif_markers(data)
        assert result["exif_presente"] is True

    def test_non_jpeg(self):
        result = detect_exif_markers(b'\x89PNG' + b'\x00' * 100)
        assert result["exif_presente"] is False


class TestAnalyzeImageBytes:
    def test_jpeg_analysis(self):
        data = b'\xff\xd8\xff\xe0' + b'\x00' * 100 + b'\xff\xd9'
        result = analyze_image_bytes(data)
        assert result["formato_rilevato"] == "JPEG"
        assert result["hash_sha256"] is not None
        assert result["dimensione_bytes"] == len(data)
        assert "entropia_globale" in result
