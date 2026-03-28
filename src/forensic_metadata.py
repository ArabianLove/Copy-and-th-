"""
Forensic Metadata Analysis Module
Analisi forense di metadati, dati embedded e indicatori steganografici
per risorse multimediali online (YouTube, immagini, audio).
"""

import re
import json
import struct
import hashlib
import base64
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse, parse_qs

import requests
from bs4 import BeautifulSoup


# --- URL Forensics ---

def parse_youtube_url(url: str) -> Dict[str, Any]:
    """
    Analisi forense di un URL YouTube/YouTube Music.
    Estrae video ID, parametri, piattaforma e genera fingerprint.

    Args:
        url: URL completo di YouTube o YouTube Music.

    Returns:
        Dizionario con tutti i metadati estraibili dall'URL.
    """
    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    video_id = None
    # Standard watch URL
    if "v" in params:
        video_id = params["v"][0]
    # Short URL (youtu.be/ID)
    elif parsed.hostname in ("youtu.be",):
        video_id = parsed.path.lstrip("/")
    # Embed URL
    elif "/embed/" in parsed.path:
        video_id = parsed.path.split("/embed/")[-1].split("?")[0]

    platform = "unknown"
    if parsed.hostname:
        if "music.youtube" in parsed.hostname:
            platform = "youtube_music"
        elif "youtube.com" in parsed.hostname or "youtu.be" in parsed.hostname:
            platform = "youtube"

    result = {
        "url_originale": url,
        "piattaforma": platform,
        "hostname": parsed.hostname,
        "schema": parsed.scheme,
        "path": parsed.path,
        "video_id": video_id,
        "parametri": {k: v[0] if len(v) == 1 else v for k, v in params.items()},
        "fragment": parsed.fragment or None,
    }

    if video_id:
        result["video_id_analisi"] = analyze_video_id(video_id)
        result["url_derivati"] = generate_derived_urls(video_id)

    return result


def analyze_video_id(video_id: str) -> Dict[str, Any]:
    """
    Analisi forense dell'ID video YouTube.
    L'ID è un Base64url-encoded 64-bit integer.

    Args:
        video_id: ID del video YouTube (11 caratteri).

    Returns:
        Analisi dettagliata dell'ID.
    """
    analysis = {
        "id": video_id,
        "lunghezza": len(video_id),
        "formato_valido": bool(re.match(r'^[A-Za-z0-9_-]{11}$', video_id)),
        "charset_usato": categorize_charset(video_id),
        "entropia_shannon": calculate_shannon_entropy(video_id),
        "hash_sha256": hashlib.sha256(video_id.encode()).hexdigest(),
        "hash_md5": hashlib.md5(video_id.encode()).hexdigest(),
    }

    # Tentativo di decodifica Base64
    try:
        padded = video_id + "=" * (4 - len(video_id) % 4)
        decoded_bytes = base64.urlsafe_b64decode(padded)
        analysis["base64_decoded_hex"] = decoded_bytes.hex()
        analysis["base64_decoded_length"] = len(decoded_bytes)
        if len(decoded_bytes) == 8:
            value = struct.unpack(">Q", decoded_bytes)[0]
            analysis["valore_numerico_uint64"] = value
    except Exception:
        analysis["base64_decoded_hex"] = None

    return analysis


def categorize_charset(text: str) -> Dict[str, int]:
    """Categorizza i caratteri usati in un testo."""
    cats = {"maiuscole": 0, "minuscole": 0, "cifre": 0, "speciali": 0}
    for c in text:
        if c.isupper():
            cats["maiuscole"] += 1
        elif c.islower():
            cats["minuscole"] += 1
        elif c.isdigit():
            cats["cifre"] += 1
        else:
            cats["speciali"] += 1
    return cats


def calculate_shannon_entropy(data: str) -> float:
    """Calcola l'entropia di Shannon di una stringa."""
    if not data:
        return 0.0
    import math
    freq = {}
    for c in data:
        freq[c] = freq.get(c, 0) + 1
    length = len(data)
    entropy = 0.0
    for count in freq.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    return round(entropy, 4)


def generate_derived_urls(video_id: str) -> Dict[str, str]:
    """
    Genera tutti gli URL derivati per raccolta forense OSINT.

    Args:
        video_id: ID del video YouTube.

    Returns:
        Dizionario di URL derivati per analisi.
    """
    return {
        "watch_url": f"https://www.youtube.com/watch?v={video_id}",
        "music_url": f"https://music.youtube.com/watch?v={video_id}",
        "embed_url": f"https://www.youtube.com/embed/{video_id}",
        "nocookie_embed": f"https://www.youtube-nocookie.com/embed/{video_id}",
        "oembed_json": f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=json",
        "oembed_xml": f"https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={video_id}&format=xml",
        "thumbnail_default": f"https://i.ytimg.com/vi/{video_id}/default.jpg",
        "thumbnail_mq": f"https://i.ytimg.com/vi/{video_id}/mqdefault.jpg",
        "thumbnail_hq": f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg",
        "thumbnail_sd": f"https://i.ytimg.com/vi/{video_id}/sddefault.jpg",
        "thumbnail_maxres": f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
        "thumbnail_frame_0": f"https://i.ytimg.com/vi/{video_id}/0.jpg",
        "thumbnail_frame_1": f"https://i.ytimg.com/vi/{video_id}/1.jpg",
        "thumbnail_frame_2": f"https://i.ytimg.com/vi/{video_id}/2.jpg",
        "thumbnail_frame_3": f"https://i.ytimg.com/vi/{video_id}/3.jpg",
        "rss_feed": f"https://www.youtube.com/feeds/videos.xml?video_id={video_id}",
    }


# --- HTTP Metadata Forensics ---

def fetch_resource_metadata(url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    Raccolta forense di metadati HTTP da una risorsa.

    Args:
        url: URL della risorsa da analizzare.
        timeout: Timeout in secondi.

    Returns:
        Metadati HTTP completi con analisi forense.
    """
    result = {
        "url": url,
        "timestamp_analisi": datetime.now(timezone.utc).isoformat(),
        "raggiungibile": False,
    }

    try:
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        result["raggiungibile"] = True
        result["status_code"] = response.status_code
        result["headers"] = dict(response.headers)
        result["url_finale"] = response.url
        result["redirect_chain"] = [r.url for r in response.history]

        # Analisi header forensi
        headers = response.headers
        result["analisi_headers"] = {
            "content_type": headers.get("Content-Type"),
            "content_length": headers.get("Content-Length"),
            "server": headers.get("Server"),
            "last_modified": headers.get("Last-Modified"),
            "etag": headers.get("ETag"),
            "cache_control": headers.get("Cache-Control"),
            "x_served_by": headers.get("X-Served-By"),
            "x_cache": headers.get("X-Cache"),
            "alt_svc": headers.get("Alt-Svc"),
            "strict_transport_security": headers.get("Strict-Transport-Security"),
            "content_security_policy": headers.get("Content-Security-Policy"),
        }

    except requests.RequestException as e:
        result["errore"] = str(e)

    return result


# --- HTML Metadata Extraction ---

def extract_page_metadata(html_content: str) -> Dict[str, Any]:
    """
    Estrae tutti i metadati embedded da contenuto HTML.
    Include Open Graph, Twitter Cards, JSON-LD, meta tags, itemprop.

    Args:
        html_content: Contenuto HTML grezzo.

    Returns:
        Dizionario strutturato con tutti i metadati trovati.
    """
    soup = BeautifulSoup(html_content, "html.parser")
    result = {}

    # Title
    title_tag = soup.find("title")
    result["title"] = title_tag.get_text() if title_tag else None

    # Open Graph
    og_tags = soup.find_all("meta", property=re.compile(r"^og:"))
    result["open_graph"] = {
        tag.get("property"): tag.get("content") for tag in og_tags
    }

    # Twitter Cards
    tw_tags = soup.find_all("meta", attrs={"name": re.compile(r"^twitter:")})
    result["twitter_cards"] = {
        tag.get("name"): tag.get("content") for tag in tw_tags
    }

    # itemprop (Schema.org microdata)
    item_tags = soup.find_all("meta", itemprop=True)
    result["itemprop"] = {
        tag.get("itemprop"): tag.get("content") for tag in item_tags
    }

    # JSON-LD structured data
    json_ld_scripts = soup.find_all("script", type="application/ld+json")
    result["json_ld"] = []
    for script in json_ld_scripts:
        try:
            result["json_ld"].append(json.loads(script.string))
        except (json.JSONDecodeError, TypeError):
            result["json_ld"].append({"raw": script.string})

    # Link tags (canonical, alternate, etc.)
    link_tags = soup.find_all("link", rel=True)
    result["link_tags"] = [
        {"rel": " ".join(tag.get("rel", [])), "href": tag.get("href"),
         "type": tag.get("type"), "hreflang": tag.get("hreflang")}
        for tag in link_tags
    ]

    # Standard meta tags
    meta_tags = soup.find_all("meta", attrs={"name": True})
    result["meta_tags"] = {
        tag.get("name"): tag.get("content") for tag in meta_tags
        if not tag.get("name", "").startswith("twitter:")
    }

    return result


# --- Image/Binary Steganography Indicators ---

def analyze_image_bytes(data: bytes) -> Dict[str, Any]:
    """
    Analisi forense di dati immagine per indicatori steganografici.

    Args:
        data: Bytes grezzi dell'immagine.

    Returns:
        Report di analisi con indicatori forensi.
    """
    result = {
        "dimensione_bytes": len(data),
        "hash_sha256": hashlib.sha256(data).hexdigest(),
        "hash_md5": hashlib.md5(data).hexdigest(),
        "magic_bytes": data[:16].hex() if len(data) >= 16 else data.hex(),
        "formato_rilevato": detect_image_format(data),
    }

    # Cerca dati dopo il marker EOF
    eof_analysis = detect_appended_data(data)
    result["dati_appendici"] = eof_analysis

    # Analisi LSB (Least Significant Bit) basica
    result["entropia_globale"] = calculate_byte_entropy(data)

    # Cerca stringhe leggibili embedded
    result["stringhe_embedded"] = extract_readable_strings(data, min_length=8)

    # EXIF marker detection
    result["marcatori_exif"] = detect_exif_markers(data)

    return result


def detect_image_format(data: bytes) -> str:
    """Rileva il formato immagine dai magic bytes."""
    signatures = {
        b'\xff\xd8\xff': "JPEG",
        b'\x89PNG\r\n\x1a\n': "PNG",
        b'GIF87a': "GIF87a",
        b'GIF89a': "GIF89a",
        b'RIFF': "WEBP",
        b'BM': "BMP",
        b'\x00\x00\x01\x00': "ICO",
        b'\x49\x49\x2a\x00': "TIFF (little-endian)",
        b'\x4d\x4d\x00\x2a': "TIFF (big-endian)",
    }
    for sig, fmt in signatures.items():
        if data[:len(sig)] == sig:
            if fmt == "WEBP" and len(data) > 8:
                if data[8:12] == b'WEBP':
                    return "WEBP"
            elif fmt != "WEBP":
                return fmt
    return "sconosciuto"


def detect_appended_data(data: bytes) -> Dict[str, Any]:
    """
    Rileva dati appendici dopo i marker EOF (indicatore steganografico).

    Per JPEG: cerca FFD9 (End Of Image).
    Per PNG: cerca IEND chunk.
    """
    result = {"trovati": False, "tipo_file": None, "offset_eof": None, "bytes_extra": 0}

    # JPEG EOF: FFD9
    if data[:2] == b'\xff\xd8':
        result["tipo_file"] = "JPEG"
        eof_pos = data.rfind(b'\xff\xd9')
        if eof_pos != -1 and eof_pos + 2 < len(data):
            result["trovati"] = True
            result["offset_eof"] = eof_pos + 2
            result["bytes_extra"] = len(data) - (eof_pos + 2)
            extra = data[eof_pos + 2:]
            result["anteprima_extra_hex"] = extra[:64].hex()

    # PNG EOF: IEND
    elif data[:4] == b'\x89PNG':
        result["tipo_file"] = "PNG"
        iend_pos = data.find(b'IEND')
        if iend_pos != -1:
            # IEND chunk: 4 bytes length + 4 bytes 'IEND' + 4 bytes CRC = +12 from length start
            # But we found 'IEND' at iend_pos, actual end is iend_pos + 4 (IEND) + 4 (CRC)
            eof_pos = iend_pos + 8
            if eof_pos < len(data):
                result["trovati"] = True
                result["offset_eof"] = eof_pos
                result["bytes_extra"] = len(data) - eof_pos
                extra = data[eof_pos:]
                result["anteprima_extra_hex"] = extra[:64].hex()

    return result


def calculate_byte_entropy(data: bytes) -> float:
    """Calcola l'entropia di Shannon sui byte (indicatore di dati nascosti)."""
    import math
    if not data:
        return 0.0
    freq = [0] * 256
    for b in data:
        freq[b] += 1
    length = len(data)
    entropy = 0.0
    for count in freq:
        if count > 0:
            p = count / length
            entropy -= p * math.log2(p)
    return round(entropy, 4)


def extract_readable_strings(data: bytes, min_length: int = 8) -> List[str]:
    """Estrae stringhe ASCII leggibili da dati binari."""
    pattern = re.compile(rb'[\x20-\x7e]{%d,}' % min_length)
    matches = pattern.findall(data)
    # Limita a 50 risultati per evitare output eccessivo
    return [m.decode("ascii", errors="replace") for m in matches[:50]]


def detect_exif_markers(data: bytes) -> Dict[str, Any]:
    """Rileva la presenza di segmenti EXIF in dati JPEG."""
    result = {"exif_presente": False, "segmenti_app": []}

    if not data or data[:2] != b'\xff\xd8':
        return result

    pos = 2
    while pos < len(data) - 1:
        if data[pos] != 0xff:
            break
        marker = data[pos:pos + 2]
        marker_hex = marker.hex()

        if marker == b'\xff\xd9':  # EOI
            break
        if marker == b'\xff\xda':  # SOS - start of scan data
            break

        if pos + 3 < len(data):
            seg_length = struct.unpack(">H", data[pos + 2:pos + 4])[0]
            seg_name = None

            if marker == b'\xff\xe1':  # APP1 - EXIF
                result["exif_presente"] = True
                seg_name = "APP1/EXIF"
            elif marker == b'\xff\xe0':
                seg_name = "APP0/JFIF"
            elif 0xe2 <= data[pos + 1] <= 0xef:
                seg_name = f"APP{data[pos+1] - 0xe0}"
            elif marker == b'\xff\xfe':
                seg_name = "COM (commento)"
                comment_data = data[pos + 4:pos + 2 + seg_length]
                seg_name += f": {comment_data[:100].decode('ascii', errors='replace')}"

            if seg_name:
                result["segmenti_app"].append({
                    "marker": marker_hex,
                    "nome": seg_name,
                    "offset": pos,
                    "lunghezza": seg_length,
                })

            pos += 2 + seg_length
        else:
            break

    return result


# --- Full Forensic Report ---

def generate_forensic_report(url: str) -> Dict[str, Any]:
    """
    Genera un report forense completo per un URL YouTube/media.

    Args:
        url: URL da analizzare.

    Returns:
        Report forense strutturato completo.
    """
    report = {
        "report_forense": {
            "versione": "1.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "analista": "forensic_metadata_module",
        }
    }

    # 1. Analisi URL
    report["analisi_url"] = parse_youtube_url(url)

    # 2. Metadati HTTP per URL derivati
    video_id = report["analisi_url"].get("video_id")
    if video_id:
        derived = report["analisi_url"].get("url_derivati", {})

        # Analisi thumbnail (più probabile sia raggiungibile)
        thumbnail_reports = {}
        for key in ("thumbnail_hq", "thumbnail_default", "thumbnail_maxres"):
            thumb_url = derived.get(key)
            if thumb_url:
                meta = fetch_resource_metadata(thumb_url)
                thumbnail_reports[key] = meta

                # Se raggiungibile, scarica e analizza per stego
                if meta.get("raggiungibile") and meta.get("status_code") == 200:
                    try:
                        resp = requests.get(thumb_url, timeout=10)
                        if resp.status_code == 200:
                            thumbnail_reports[key]["analisi_immagine"] = analyze_image_bytes(resp.content)
                    except requests.RequestException:
                        pass

        report["analisi_thumbnail"] = thumbnail_reports

        # oEmbed
        oembed_url = derived.get("oembed_json")
        if oembed_url:
            report["oembed"] = fetch_resource_metadata(oembed_url)
            try:
                resp = requests.get(oembed_url, timeout=10)
                if resp.status_code == 200:
                    report["oembed"]["dati"] = resp.json()
            except (requests.RequestException, json.JSONDecodeError):
                pass

    return report
