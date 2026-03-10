#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Predator Hunt Arsenale Omnibus vFINALE (Improved)

Android Termux - All Modules Integrated.
Forensic analysis tool for defensive security and educational use.

Modules:
  [01] YARA  [02] Network  [03] Memory  [04] Frida  [05] Radare2
  [06] AndroGuard  [07] BulkExtract  [08] Database  [09] TLS-Fingerprint
  [10] ML-Behavioral  [11] QEMU-Sandbox  [12] StegoHunter  [13] VaultHunter
  [14] PerceptualHash  [15] VideoAnalyzer  [16] Blockchain
  [17] CryptoBreaker  [18] PCAP-Reconstructor

Usage:
  python predator_arsenale.py /sdcard/Download
  python predator_arsenale.py --apk /sdcard/app.apk --pcap capture.pcap /sdcard
"""

import argparse
import asyncio
import hashlib
import json
import logging
import math
import os
import re
import sqlite3
import stat
import struct
import subprocess
import sys
import uuid
import zipfile
from datetime import datetime, timezone
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional dependency imports with availability flags
# ---------------------------------------------------------------------------

try:
    import aiofiles
    AIOFILES_AVAILABLE = True
except ImportError:
    AIOFILES_AVAILABLE = False

try:
    import frida
    FRIDA_AVAILABLE = True
except ImportError:
    FRIDA_AVAILABLE = False

try:
    from scapy.all import sniff, IP, TCP, UDP, Raw
    SCAPY_AVAILABLE = True
except ImportError:
    SCAPY_AVAILABLE = False

try:
    import r2pipe
    R2_AVAILABLE = True
except ImportError:
    R2_AVAILABLE = False

try:
    from androguard.core.apk import APK
    ANDROGUARD_AVAILABLE = True
except ImportError:
    ANDROGUARD_AVAILABLE = False

try:
    from PIL import Image
    import imagehash
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

try:
    import magic as python_magic
    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False

# ---------------------------------------------------------------------------
# Platform detection (safe, no side effects)
# ---------------------------------------------------------------------------

IS_ANDROID = os.path.exists("/sdcard") or os.path.exists("/system/build.prop")
IS_ROOT = os.geteuid() == 0 if hasattr(os, "geteuid") else False


def _default_output_dir() -> str:
    if IS_ANDROID:
        return "/sdcard/PredatorHunt"
    return os.path.join(os.path.expanduser("~"), "PredatorHunt")


# ---------------------------------------------------------------------------
# ANSI Colors
# ---------------------------------------------------------------------------

class Colors:
    R = "\033[91m"
    G = "\033[92m"
    Y = "\033[93m"
    B = "\033[94m"
    M = "\033[95m"
    C = "\033[96m"
    W = "\033[97m"
    END = "\033[0m"
    BOLD = "\033[1m"


# ---------------------------------------------------------------------------
# Core data model
# ---------------------------------------------------------------------------

@dataclass
class ThreatArtifact:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:16])
    timestamp: str = field(
        default_factory=lambda: datetime.now(tz=timezone.utc).isoformat()
    )
    tactic: str = ""
    technique: str = ""
    severity: int = 0
    path: str = ""
    ioc_type: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    yara_matches: List[str] = field(default_factory=list)
    entropy: float = 0.0
    hash_sha256: str = ""
    source: str = "arsenale"
    ml_score: float = 0.0


# ---------------------------------------------------------------------------
# Shared utility
# ---------------------------------------------------------------------------

def shannon_entropy(data: bytes) -> float:
    """
    Compute normalised Shannon entropy of *data* (0.0 - 1.0).

    Args:
        data: Raw bytes to analyse.

    Returns:
        Normalised entropy value.
    """
    if not data:
        return 0.0
    length = len(data)
    freq = [0] * 256
    for byte in data:
        freq[byte] += 1
    entropy = 0.0
    for count in freq:
        if count:
            p = count / length
            entropy -= p * math.log2(p)
    return entropy / 8.0


def compute_file_hash(filepath: str, algorithm: str = "sha256") -> str:
    """
    Compute a hex digest for *filepath*.

    Args:
        filepath: Path to the file.
        algorithm: Hash algorithm name (sha256, md5, sha1).

    Returns:
        Hex digest string.
    """
    h = hashlib.new(algorithm)
    with open(filepath, "rb") as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


async def _read_file_bytes(filepath: str) -> bytes:
    """Read a file as bytes, using aiofiles when available."""
    if AIOFILES_AVAILABLE:
        async with aiofiles.open(filepath, "rb") as f:
            return await f.read()
    with open(filepath, "rb") as f:
        return f.read()


async def _read_file_text(filepath: str) -> str:
    """Read a file as text (lossy), using aiofiles when available."""
    if AIOFILES_AVAILABLE:
        async with aiofiles.open(filepath, "r", errors="ignore") as f:
            return await f.read()
    with open(filepath, "r", errors="ignore") as f:
        return f.read()


# ===========================================================================
# MODULE 01: YARA ENGINE
# ===========================================================================

class YaraEngine:
    """Compile and apply YARA rules for malware signature scanning."""

    def __init__(self) -> None:
        self.rules = None
        self._compile_rules()

    def _compile_rules(self) -> None:
        try:
            import yara

            rules_src = """
            rule Android_Malware_Generic {
                meta:
                    description = "Generic Android malware indicators"
                strings:
                    $a = "/system/bin/su" nocase
                    $b = "ro.debuggable" nocase
                    $c = "android/os/Process" nocase
                    $d = "Ljava/lang/Runtime;->exec" nocase
                condition:
                    any of them
            }

            rule Spyware_Indicators {
                strings:
                    $sms = "android/telephony/SmsManager" nocase
                    $location = "android/location/LocationManager" nocase
                    $record = "android/media/MediaRecorder" nocase
                condition:
                    2 of them
            }

            rule Hidden_Content {
                strings:
                    $hidden = ".hidden" nocase
                    $nomedia = ".nomedia" nocase
                    $vault = "vault" nocase
                condition:
                    any of them
            }

            rule Crypto_Wallet {
                strings:
                    $btc = /[13][a-km-zA-HJ-NP-Z1-9]{25,34}/
                    $eth = /0x[a-fA-F0-9]{40}/
                condition:
                    any of them
            }
            """
            self.rules = yara.compile(source=rules_src)
        except Exception as exc:
            logger.warning("YARA not available: %s", exc)

    def scan_file(self, filepath: str) -> List[Dict[str, Any]]:
        """
        Scan a single file against compiled YARA rules.

        Args:
            filepath: Path to the file.

        Returns:
            List of match dicts with 'rule' and 'strings' keys.
        """
        if not self.rules or not os.path.isfile(filepath):
            return []
        try:
            matches = self.rules.match(filepath)
            return [
                {"rule": m.rule, "strings": m.strings[:3]}
                for m in matches
            ]
        except Exception as exc:
            logger.debug("YARA scan failed for %s: %s", filepath, exc)
            return []


# ===========================================================================
# MODULE 02: NETWORK ARSENAL
# ===========================================================================

class NetworkArsenal:
    """Live packet capture and PCAP analysis via Scapy."""

    def __init__(self) -> None:
        self.packets: List[Dict[str, str]] = []

    async def capture_live(
        self, interface: str = "wlan0", duration: int = 30
    ) -> List[Dict[str, str]]:
        """
        Capture live traffic on *interface* for *duration* seconds.

        Args:
            interface: Network interface name.
            duration: Capture duration in seconds.

        Returns:
            List of packet summary dicts.
        """
        if not SCAPY_AVAILABLE or not IS_ROOT:
            return []

        logger.info("Capturing on %s for %ds...", interface, duration)

        def _handler(pkt):
            if IP in pkt:
                self.packets.append({
                    "src": pkt[IP].src,
                    "dst": pkt[IP].dst,
                    "proto": "TCP" if TCP in pkt else "UDP",
                    "time": datetime.now(tz=timezone.utc).isoformat(),
                })

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: sniff(iface=interface, prn=_handler, timeout=duration, store=0),
        )
        return self.packets

    async def analyze_pcap(self, pcap_path: str) -> List[Dict[str, Any]]:
        """
        Carve images from a PCAP file.

        Args:
            pcap_path: Path to the .pcap file.

        Returns:
            List of carved file dicts.
        """
        if not SCAPY_AVAILABLE:
            return []
        from scapy.all import rdpcap

        pkts = rdpcap(pcap_path)
        carved: List[Dict[str, Any]] = []
        for pkt in pkts:
            if Raw in pkt:
                payload = bytes(pkt[Raw].load)
                if payload.startswith(b"\x89PNG"):
                    carved.append({"type": "png", "size": len(payload)})
                elif payload.startswith(b"\xff\xd8"):
                    carved.append({"type": "jpg", "size": len(payload)})
        return carved


# ===========================================================================
# MODULE 03: MEMORY FORENSICS
# ===========================================================================

class MemoryForensics:
    """Acquire and analyse memory dumps (requires root)."""

    MAX_DUMP_BYTES = 256 * 1024 * 1024  # 256 MB

    async def acquire_memory(self, output_path: Optional[str] = None) -> Optional[str]:
        """
        Dump up to 256 MB from /proc/kcore.

        Args:
            output_path: Destination file. Defaults to OUTPUT_DIR/memory_dump.raw.

        Returns:
            Path to the dump file, or None.
        """
        if not IS_ROOT:
            return None
        out = output_path or os.path.join(_default_output_dir(), "memory_dump.raw")
        if not os.path.exists("/proc/kcore"):
            return None
        try:
            with open("/proc/kcore", "rb") as src, open(out, "wb") as dst:
                dst.write(src.read(self.MAX_DUMP_BYTES))
            return out
        except OSError as exc:
            logger.error("Memory acquisition failed: %s", exc)
            return None

    async def analyze_dump(self, dump_path: str) -> List[Dict[str, str]]:
        """
        Scan a memory dump for secret patterns.

        Args:
            dump_path: Path to the raw dump.

        Returns:
            List of finding dicts.
        """
        if not os.path.isfile(dump_path):
            return []
        findings: List[Dict[str, str]] = []
        with open(dump_path, "rb") as f:
            data = f.read()

        patterns = [
            b"password=",
            b"api_key=",
            b"secret=",
            b"-----BEGIN PRIVATE KEY-----",
        ]
        for pat in patterns:
            idx = data.find(pat)
            if idx != -1:
                context = data[max(0, idx - 20): idx + 50]
                findings.append({
                    "type": "secret_in_memory",
                    "pattern": pat.decode(),
                    "context": context.decode("utf-8", errors="ignore"),
                })
        return findings


# ===========================================================================
# MODULE 04: FRIDA DYNAMIC INSTRUMENTATION
# ===========================================================================

class FridaDynamic:
    """Frida-based dynamic analysis of running Android apps."""

    def __init__(self) -> None:
        self.device = None
        self.findings: List[Dict[str, Any]] = []

    async def connect(self) -> bool:
        """
        Connect to a USB Frida device.

        Returns:
            True if connected successfully.
        """
        if not FRIDA_AVAILABLE:
            return False
        try:
            self.device = frida.get_usb_device()
            return True
        except Exception as exc:
            logger.warning("Frida connection failed: %s", exc)
            return False

    async def instrument_app(self, package: str, duration: int = 30) -> None:
        """
        Instrument *package* for *duration* seconds, hooking suspicious APIs.

        Args:
            package: Android package name.
            duration: Observation window in seconds.
        """
        if not self.device:
            return

        try:
            pid = self.device.spawn([package])
            session = self.device.attach(pid)

            script = session.create_script("""
                Java.perform(function() {
                    var TelephonyManager = Java.use(
                        'android.telephony.TelephonyManager'
                    );
                    TelephonyManager.getDeviceId.implementation = function() {
                        send({type: 'spyware', api: 'getDeviceId'});
                        return this.getDeviceId();
                    };
                });
            """)

            def _on_message(message, _data):
                if message.get("type") == "send":
                    self.findings.append(message["payload"])

            script.on("message", _on_message)
            script.load()
            self.device.resume(pid)
            await asyncio.sleep(duration)
            session.detach()
        except Exception as exc:
            logger.warning("Frida instrumentation error: %s", exc)


# ===========================================================================
# MODULE 05: RADARE2 BINARY ANALYSIS
# ===========================================================================

class RadareAnalyzer:
    """Extract URLs and suspicious strings from binaries via r2pipe."""

    async def analyze_binary(self, filepath: str) -> List[Dict[str, str]]:
        """
        Analyse a binary with Radare2.

        Args:
            filepath: Path to the binary.

        Returns:
            List of finding dicts.
        """
        if not R2_AVAILABLE or not os.path.isfile(filepath):
            return []

        findings: List[Dict[str, str]] = []
        r2 = None
        try:
            r2 = r2pipe.open(filepath)
            r2.cmd("aaa")

            strings = r2.cmdj("izj")
            if strings:
                for s in strings:
                    value = s.get("string", "")
                    if re.match(r"https?://", value):
                        findings.append({"type": "url", "value": value})
        except Exception as exc:
            logger.debug("Radare2 analysis failed for %s: %s", filepath, exc)
        finally:
            if r2:
                r2.quit()
        return findings


# ===========================================================================
# MODULE 06: ANDROGUARD APK ANALYSIS
# ===========================================================================

class AndroAnalyzer:
    """Deep APK analysis via AndroGuard."""

    async def analyze_apk(self, apk_path: str) -> Optional[Dict[str, Any]]:
        """
        Analyse an APK for permissions and activities.

        Args:
            apk_path: Path to the .apk file.

        Returns:
            Analysis dict or None.
        """
        if not ANDROGUARD_AVAILABLE or not os.path.isfile(apk_path):
            return None

        try:
            apk = APK(apk_path)
            perms = apk.get_permissions()
            dangerous = [
                p for p in perms
                if any(x in p for x in ["SMS", "LOCATION", "CAMERA", "RECORD"])
            ]
            return {
                "package": apk.get_package(),
                "permissions": perms,
                "dangerous_perms": dangerous,
                "activities": apk.get_activities(),
            }
        except Exception as exc:
            logger.debug("AndroGuard analysis failed: %s", exc)
            return None


# ===========================================================================
# MODULE 07: BULK DATA EXTRACTOR
# ===========================================================================

class BulkExtractor:
    """Extract emails, crypto wallets, URLs, phone numbers, GPS coords."""

    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

    def __init__(self) -> None:
        self.patterns: Dict[str, re.Pattern] = {
            "email": re.compile(
                r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z]{2,}\b", re.I
            ),
            "bitcoin": re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b"),
            "ethereum": re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
            "monero": re.compile(r"\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b"),
            "phone": re.compile(
                r"(\+\d{1,3}[-.]?)?\(?\d{3}\)?[-.]?\d{3}[-.]?\d{4}"
            ),
            "url": re.compile(r"https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+"),
            "coordinates": re.compile(
                r"-?\d{1,3}\.\d{4,},\s*-?\d{1,3}\.\d{4,}"
            ),
        }

    async def scan_file(self, filepath: str) -> Dict[str, List[str]]:
        """
        Extract pattern matches from a text file.

        Args:
            filepath: Path to the file.

        Returns:
            Dict mapping pattern names to deduplicated match lists.
        """
        if not os.path.isfile(filepath):
            return {}
        if os.path.getsize(filepath) > self.MAX_FILE_SIZE:
            return {}

        findings: Dict[str, List[str]] = {}
        try:
            content = await _read_file_text(filepath)
            for dtype, pattern in self.patterns.items():
                matches = pattern.findall(content)
                if matches:
                    findings[dtype] = list(set(matches))[:10]
        except Exception as exc:
            logger.debug("Bulk extraction failed for %s: %s", filepath, exc)
        return findings


# ===========================================================================
# MODULE 08: DATABASE FORENSICS
# ===========================================================================

class DatabaseForensics:
    """Inspect SQLite databases for tables with sensitive names."""

    KEYWORDS = [
        "password", "secret", "key", "token",
        "credential", "auth", "message", "contact",
    ]

    async def analyze_sqlite(self, db_path: str) -> Optional[Dict[str, Any]]:
        """
        Analyse a SQLite database file.

        Args:
            db_path: Path to the .db / .sqlite file.

        Returns:
            Analysis dict or None.
        """
        if not os.path.isfile(db_path):
            return None

        try:
            conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
            try:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = [r[0] for r in cursor.fetchall()]
                suspicious = [
                    t for t in tables
                    if any(k in t.lower() for k in self.KEYWORDS)
                ]
                return {
                    "tables": tables,
                    "suspicious_tables": suspicious,
                    "path": db_path,
                }
            finally:
                conn.close()
        except Exception as exc:
            return {"error": str(exc)}


# ===========================================================================
# MODULE 09: TLS FINGERPRINT
# ===========================================================================

class TLSFingerprint:
    """Check JA3 hashes against known malware fingerprints."""

    def __init__(self) -> None:
        self.malware_ja3: Dict[str, str] = {
            "b32309a26951912be7dba376398abc3b": "Dridex",
            "6734f37431670b3ab4292b8f60f29984": "TrickBot",
        }

    def check_ja3(self, ja3_hash: str) -> Optional[str]:
        """
        Check if a JA3 hash is associated with known malware.

        Args:
            ja3_hash: The JA3 hash string.

        Returns:
            Malware name or None.
        """
        return self.malware_ja3.get(ja3_hash)


# ===========================================================================
# MODULE 10: BEHAVIORAL ML
# ===========================================================================

class BehavioralML:
    """Detect process resource anomalies (CPU / memory spikes)."""

    def detect_anomalies(
        self, processes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Flag processes with abnormally high resource usage.

        Args:
            processes: List of process info dicts.

        Returns:
            List of anomaly dicts.
        """
        anomalies: List[Dict[str, Any]] = []
        for proc in processes:
            cpu = proc.get("cpu_percent", 0)
            mem = proc.get("memory_percent", 0)
            if cpu > 80 or mem > 10:
                anomalies.append({
                    "pid": proc.get("pid"),
                    "name": proc.get("name"),
                    "cpu": cpu,
                    "mem": mem,
                    "type": "resource_anomaly",
                })
        return anomalies


# ===========================================================================
# MODULE 11: QEMU SANDBOX (placeholder)
# ===========================================================================

class QEMUSandbox:
    """Placeholder for QEMU-based dynamic APK analysis."""

    async def analyze_apk(self, apk_path: str) -> List[Dict[str, str]]:
        """
        Run an APK in a QEMU sandbox (placeholder).

        Args:
            apk_path: Path to the .apk file.

        Returns:
            List of findings.
        """
        if not os.path.isfile(apk_path):
            return []
        return [{"type": "sandbox_placeholder", "file": apk_path}]


# ===========================================================================
# MODULE 12: STEGO HUNTER
# ===========================================================================

class StegoHunter:
    """Detect steganography in image files."""

    SIGNATURES = [b"steghide", b"outguess", b"OpenStego"]

    async def analyze_image(
        self, image_path: str, quarantine_dir: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Analyse an image for steganographic indicators.

        Args:
            image_path: Path to the image file.
            quarantine_dir: Directory for extracted hidden data.

        Returns:
            Analysis dict or None.
        """
        if not os.path.isfile(image_path):
            return None

        result: Dict[str, Any] = {
            "path": image_path,
            "suspicious": False,
            "indicators": [],
            "hidden_data": False,
        }

        data = await _read_file_bytes(image_path)

        # Check stego tool signatures
        for sig in self.SIGNATURES:
            if sig in data:
                result["suspicious"] = True
                result["indicators"].append(f"Signature: {sig.decode()}")

        # Check for data appended after JPEG EOF marker
        if image_path.lower().endswith((".jpg", ".jpeg")):
            eof = data.find(b"\xff\xd9")
            if eof != -1 and len(data) > eof + 2:
                trailing = len(data) - (eof + 2)
                if trailing > 100:
                    result["suspicious"] = True
                    result["hidden_data"] = True
                    result["hidden_bytes"] = trailing
                    result["indicators"].append(
                        f"Data after EOF: {trailing} bytes"
                    )
                    if quarantine_dir:
                        os.makedirs(quarantine_dir, exist_ok=True)
                        qpath = os.path.join(
                            quarantine_dir,
                            f"hidden_{os.path.basename(image_path)}.bin",
                        )
                        with open(qpath, "wb") as qf:
                            qf.write(data[eof + 2:])
                        result["extracted"] = qpath

        # Entropy of last 1 KB
        if data:
            entropy = shannon_entropy(data[-1024:])
            result["entropy"] = round(entropy, 4)
            if entropy > 0.95:
                result["suspicious"] = True
                result["indicators"].append(f"High entropy: {entropy:.3f}")

        return result


# ===========================================================================
# MODULE 13: VAULT HUNTER
# ===========================================================================

class VaultHunter:
    """Find hidden vault apps and suspicious directory structures."""

    VAULT_APPS = [
        "com.hld.anzenbokusu",
        "com.calculator.photo.vault",
        "com.hideapp.privatephoto",
        "com.kii.safe",
        "com.domobile.applock",
    ]
    SUSPICIOUS_DIR_NAMES = ["hidden", "vault", "secret", ".nomedia"]

    def scan(self, base_path: str) -> List[Dict[str, Any]]:
        """
        Scan for vault apps and suspicious directory structures.

        Args:
            base_path: Root directory to scan.

        Returns:
            List of finding dicts.
        """
        findings: List[Dict[str, Any]] = []

        # Check installed vault apps (requires root)
        if IS_ROOT and os.path.isdir("/data/data"):
            try:
                for pkg in os.listdir("/data/data"):
                    if any(v in pkg for v in self.VAULT_APPS):
                        findings.append({
                            "type": "vault_app",
                            "path": f"/data/data/{pkg}",
                            "severity": 90,
                        })
            except PermissionError:
                pass

        # Check for suspicious dirs and double-extension files
        for root, dirs, files in os.walk(base_path):
            for d in dirs:
                lower_d = d.lower()
                if (
                    any(s in lower_d for s in self.SUSPICIOUS_DIR_NAMES)
                    or d.startswith(".")
                ):
                    findings.append({
                        "type": "suspicious_directory",
                        "path": os.path.join(root, d),
                        "severity": 70,
                    })

            for f in files:
                fl = f.lower()
                if (
                    ".jpg." in fl
                    or ".png." in fl
                    or fl.endswith((".jpg.exe", ".png.zip"))
                ):
                    findings.append({
                        "type": "double_extension",
                        "path": os.path.join(root, f),
                        "severity": 95,
                    })

        return findings


# ===========================================================================
# MODULE 14: PERCEPTUAL HASH DUPLICATE FINDER
# ===========================================================================

class PerceptualHunter:
    """Find visually similar images using perceptual hashing."""

    IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")

    async def find_duplicates(
        self, directory: str
    ) -> List[Dict[str, Any]]:
        """
        Walk *directory* and group images by perceptual hash.

        Args:
            directory: Root directory to scan.

        Returns:
            List of duplicate-pair dicts.
        """
        if not PIL_AVAILABLE:
            return []

        hashes: Dict[str, str] = {}
        duplicates: List[Dict[str, Any]] = []

        for root, _, files in os.walk(directory):
            for f in files:
                if not f.lower().endswith(self.IMAGE_EXTENSIONS):
                    continue
                path = os.path.join(root, f)
                try:
                    img = Image.open(path)
                    ahash = str(imagehash.average_hash(img))
                    if ahash in hashes:
                        duplicates.append({
                            "type": "perceptual_duplicate",
                            "original": hashes[ahash],
                            "duplicate": path,
                            "hash_type": "ahash",
                            "severity": 50,
                        })
                    else:
                        hashes[ahash] = path
                except Exception:
                    continue

        return duplicates


# ===========================================================================
# MODULE 15: VIDEO ANALYZER
# ===========================================================================

class VideoAnalyzer:
    """Analyse video files for hidden payloads and metadata."""

    def __init__(self) -> None:
        try:
            result = subprocess.run(
                ["which", "ffmpeg"], capture_output=True, check=False
            )
            self.has_ffmpeg = result.returncode == 0
        except FileNotFoundError:
            self.has_ffmpeg = False

    async def analyze(
        self,
        video_path: str,
        quarantine_dir: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Analyse a video file for suspicious indicators.

        Args:
            video_path: Path to the video file.
            quarantine_dir: Directory for extracted frames.

        Returns:
            Analysis dict or None.
        """
        if not os.path.isfile(video_path):
            return None

        result: Dict[str, Any] = {
            "path": video_path,
            "format": "unknown",
            "suspicious": False,
            "indicators": [],
            "metadata": {},
        }

        data = await _read_file_bytes(video_path)
        if not data:
            return result

        # Detect format from magic bytes
        if b"ftyp" in data[:12]:
            result["format"] = "MP4/MOV"
        elif data[:4] == b"RIFF":
            result["format"] = "AVI"
        elif data[:4] == b"\x1aE\xdf\xa3":
            result["format"] = "MKV"

        # Check entropy of the middle section
        mid = len(data) // 2
        sample = data[mid: mid + 65536]
        entropy = shannon_entropy(sample)
        result["entropy"] = round(entropy, 4)
        if entropy > 0.98:
            result["suspicious"] = True
            result["indicators"].append(
                "Very high entropy - possible encrypted payload"
            )

        # Frame extraction (safe subprocess, no shell=True)
        if self.has_ffmpeg and PIL_AVAILABLE and quarantine_dir:
            await self._extract_frames(video_path, result, quarantine_dir)
        else:
            result["metadata"] = self._extract_strings(data)

        return result

    async def _extract_frames(
        self,
        video_path: str,
        result: Dict[str, Any],
        quarantine_dir: str,
    ) -> None:
        """Extract key frames and check them with StegoHunter."""
        tag = hashlib.sha256(video_path.encode()).hexdigest()[:8]
        temp_dir = os.path.join(quarantine_dir, f"video_frames_{tag}")
        os.makedirs(temp_dir, exist_ok=True)

        frame_pattern = os.path.join(temp_dir, "frame_%03d.jpg")
        try:
            subprocess.run(
                [
                    "ffmpeg", "-i", video_path,
                    "-vf", "fps=1/10",
                    "-vframes", "3",
                    frame_pattern,
                ],
                capture_output=True,
                timeout=60,
                check=False,
            )

            stego = StegoHunter()
            for frame in sorted(os.listdir(temp_dir)):
                if frame.endswith(".jpg"):
                    frame_result = await stego.analyze_image(
                        os.path.join(temp_dir, frame)
                    )
                    if frame_result and frame_result.get("suspicious"):
                        result["suspicious"] = True
                        result["indicators"].append(
                            f"Suspicious frame: {frame}"
                        )
                        break
        except subprocess.TimeoutExpired:
            result["indicators"].append("Frame extraction timed out")
        except Exception as exc:
            result["indicators"].append(f"Frame extraction error: {exc}")

    @staticmethod
    def _extract_strings(data: bytes) -> Dict[str, Any]:
        """Extract GPS coordinates from raw video bytes."""
        metadata: Dict[str, Any] = {}
        gps = re.search(
            rb"([\+\-]?\d{1,3}\.\d+)([NS])\s*([\+\-]?\d{1,3}\.\d+)([EW])",
            data,
        )
        if gps:
            metadata["gps"] = [g.decode("ascii", errors="ignore") for g in gps.groups()]
        return metadata


# ===========================================================================
# MODULE 16: BLOCKCHAIN ANALYZER
# ===========================================================================

class BlockchainAnalyzer:
    """Extract cryptocurrency wallet addresses from files."""

    TEXT_EXTENSIONS = (".txt", ".log", ".json", ".db", ".csv")

    def __init__(self) -> None:
        self.patterns: Dict[str, re.Pattern] = {
            "btc": re.compile(r"\b[13][a-km-zA-HJ-NP-Z1-9]{25,34}\b"),
            "eth": re.compile(r"\b0x[a-fA-F0-9]{40}\b"),
            "xmr": re.compile(r"\b4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}\b"),
        }

    async def extract_wallets(
        self, directory: str
    ) -> List[Dict[str, Any]]:
        """
        Scan text files for crypto wallet addresses.

        Args:
            directory: Root directory to scan.

        Returns:
            List of finding dicts.
        """
        findings: List[Dict[str, Any]] = []
        for root, _, files in os.walk(directory):
            for f in files:
                if not f.endswith(self.TEXT_EXTENSIONS):
                    continue
                path = os.path.join(root, f)
                try:
                    content = await _read_file_text(path)
                    for coin, pattern in self.patterns.items():
                        matches = pattern.findall(content)
                        if matches:
                            findings.append({
                                "file": path,
                                "coin": coin,
                                "wallets": list(set(matches)),
                                "severity": 80 if coin == "xmr" else 60,
                            })
                except Exception:
                    continue
        return findings


# ===========================================================================
# MODULE 17: CRYPTO BREAKER
# ===========================================================================

class CryptoBreaker:
    """Attempt to crack password-protected ZIP archives."""

    COMMON_PASSWORDS = [
        "1234", "0000", "password", "123456",
        "12345678", "qwerty", "admin",
    ]

    async def crack_zip(
        self,
        zip_path: str,
        output_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Try common passwords on a ZIP file.

        Args:
            zip_path: Path to the .zip file.
            output_dir: Directory to extract to on success.

        Returns:
            Dict with 'cracked' bool and optional 'password'.
        """
        if not os.path.isfile(zip_path):
            return {"cracked": False, "error": "file not found"}

        extract_dir = output_dir or _default_output_dir()

        try:
            with zipfile.ZipFile(zip_path, "r") as zf:
                for pwd in self.COMMON_PASSWORDS:
                    try:
                        zf.extractall(path=extract_dir, pwd=pwd.encode())
                        return {
                            "cracked": True,
                            "password": pwd,
                            "file": zip_path,
                        }
                    except (RuntimeError, zipfile.BadZipFile):
                        continue
        except zipfile.BadZipFile:
            return {"cracked": False, "error": "invalid zip"}

        return {"cracked": False}


# ===========================================================================
# MODULE 18: PCAP RECONSTRUCTOR
# ===========================================================================

class PCAPReconstructor:
    """Reconstruct files (images) embedded in PCAP traffic."""

    async def reconstruct_images(
        self, pcap_path: str, output_dir: Optional[str] = None
    ) -> List[str]:
        """
        Extract images from PCAP packet payloads.

        Args:
            pcap_path: Path to the .pcap file.
            output_dir: Directory for extracted files.

        Returns:
            List of paths to extracted files.
        """
        if not SCAPY_AVAILABLE:
            return []

        out = output_dir or _default_output_dir()
        os.makedirs(out, exist_ok=True)

        from scapy.all import rdpcap, Raw

        pkts = rdpcap(pcap_path)
        files: List[str] = []

        for i, pkt in enumerate(pkts):
            if Raw not in pkt:
                continue
            payload = bytes(pkt[Raw].load)
            ext = None
            if payload.startswith(b"\x89PNG"):
                ext = "png"
            elif payload.startswith(b"\xff\xd8"):
                ext = "jpg"
            if ext:
                fname = f"reconstructed_{i}.{ext}"
                path = os.path.join(out, fname)
                with open(path, "wb") as f:
                    f.write(payload)
                files.append(path)

        return files


# ===========================================================================
# MAIN CONTROLLER
# ===========================================================================

class PredatorHunt:
    """Orchestrate all forensic modules and produce reports."""

    MAX_YARA_FILES = 200

    def __init__(self, output_dir: Optional[str] = None) -> None:
        self.output_dir = output_dir or _default_output_dir()
        self.quarantine_dir = os.path.join(self.output_dir, "quarantine")

        self.yara = YaraEngine()
        self.network = NetworkArsenal()
        self.memory = MemoryForensics()
        self.frida_mod = FridaDynamic()
        self.radare = RadareAnalyzer()
        self.andro = AndroAnalyzer()
        self.bulk = BulkExtractor()
        self.db_forensics = DatabaseForensics()
        self.tls = TLSFingerprint()
        self.ml = BehavioralML()
        self.sandbox = QEMUSandbox()
        self.stego = StegoHunter()
        self.vault = VaultHunter()
        self.perceptual = PerceptualHunter()
        self.video = VideoAnalyzer()
        self.blockchain = BlockchainAnalyzer()
        self.crypto = CryptoBreaker()
        self.pcap_recon = PCAPReconstructor()
        self.artifacts: List[ThreatArtifact] = []

    def _ensure_dirs(self) -> None:
        """Create output and quarantine directories."""
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(self.quarantine_dir, exist_ok=True)

    def _setup_db(self) -> None:
        """Create the artifacts database table if it does not exist."""
        db_path = os.path.join(self.output_dir, "arsenale.db")
        with sqlite3.connect(db_path) as conn:
            conn.execute(
                """CREATE TABLE IF NOT EXISTS artifacts (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT,
                    type TEXT,
                    path TEXT,
                    severity INTEGER,
                    metadata TEXT
                )"""
            )

    # ----- scanning pipeline -----

    async def scan(self, target_path: str) -> None:
        """
        Run the full forensic scan pipeline on *target_path*.

        Args:
            target_path: Root directory to analyse.
        """
        self._ensure_dirs()
        self._setup_db()

        self._banner()
        print(f"{Colors.Y}[*] Target: {target_path}{Colors.END}")
        print(
            f"{Colors.Y}[*] Root: {'Yes' if IS_ROOT else 'No'} | "
            f"YARA: {'Yes' if self.yara.rules else 'No'} | "
            f"PIL: {'Yes' if PIL_AVAILABLE else 'No'}{Colors.END}\n"
        )

        if not os.path.exists(target_path):
            print(f"{Colors.R}[!] Path not found: {target_path}{Colors.END}")
            return

        await self._run_vault(target_path)
        await self._run_yara(target_path)
        await self._run_stego(target_path)
        await self._run_video(target_path)
        await self._run_perceptual(target_path)
        await self._run_bulk(target_path)
        await self._run_blockchain(target_path)
        await self._run_db_forensics(target_path)
        await self._run_zip_crack(target_path)
        await self._run_memory()
        await self._run_behavioral()

        print(
            f"{Colors.C}[12-18/18] Radare2, AndroGuard, Frida, "
            f"Network, Sandbox, PCAP, TLS...{Colors.END}"
        )

        self._save_and_report()

    # ----- individual scan stages -----

    async def _run_vault(self, target: str) -> None:
        print(f"{Colors.C}[01/18] Vault Hunter & Directory Analysis...{Colors.END}")
        findings = self.vault.scan(target)
        for v in findings:
            self._add_artifact(
                v["type"], v.get("path", ""), v, v.get("severity", 50)
            )
        print(f"   Found: {len(findings)} structural elements")

    async def _run_yara(self, target: str) -> None:
        print(f"{Colors.C}[02/18] YARA Signature Scan...{Colors.END}")
        count = 0
        for root, _, files in os.walk(target):
            for f in files[: self.MAX_YARA_FILES]:
                path = os.path.join(root, f)
                matches = self.yara.scan_file(path)
                if matches:
                    self._add_artifact(
                        "yara_match", path, {"matches": str(matches)}, 85
                    )
                    count += 1
        print(f"   YARA hits: {count}")

    async def _run_stego(self, target: str) -> None:
        print(f"{Colors.C}[03/18] Steganography Analysis (Images)...{Colors.END}")
        count = 0
        for root, _, files in os.walk(target):
            for f in files:
                if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp")):
                    path = os.path.join(root, f)
                    result = await self.stego.analyze_image(
                        path, quarantine_dir=self.quarantine_dir
                    )
                    if result and result.get("suspicious"):
                        sev = 90 if result.get("hidden_data") else 75
                        self._add_artifact("steganography", path, result, sev)
                        count += 1
        print(f"   Suspicious: {count}")

    async def _run_video(self, target: str) -> None:
        print(f"{Colors.C}[04/18] Video Analysis (Frame extraction)...{Colors.END}")
        count = 0
        for root, _, files in os.walk(target):
            for f in files:
                if f.lower().endswith((".mp4", ".avi", ".mov", ".mkv", ".3gp")):
                    path = os.path.join(root, f)
                    result = await self.video.analyze(
                        path, quarantine_dir=self.quarantine_dir
                    )
                    if result and result.get("suspicious"):
                        self._add_artifact(
                            "suspicious_video", path, result, 85
                        )
                        count += 1
        print(f"   Suspicious videos: {count}")

    async def _run_perceptual(self, target: str) -> None:
        if not PIL_AVAILABLE:
            return
        print(f"{Colors.C}[05/18] Perceptual Hashing (Duplicates)...{Colors.END}")
        dups = await self.perceptual.find_duplicates(target)
        for d in dups:
            self._add_artifact(d["type"], d["duplicate"], d, d["severity"])
        print(f"   Duplicates found: {len(dups)}")

    async def _run_bulk(self, target: str) -> None:
        print(f"{Colors.C}[06/18] Bulk Data Extraction (Crypto/Email)...{Colors.END}")
        extracted = 0
        for root, _, files in os.walk(target):
            for f in files:
                if f.endswith((".txt", ".log", ".json", ".xml")):
                    path = os.path.join(root, f)
                    data = await self.bulk.scan_file(path)
                    if data:
                        extracted += sum(len(v) for v in data.values())
                        for dtype, values in data.items():
                            self._add_artifact(
                                f"extracted_{dtype}",
                                path,
                                {"count": len(values), "samples": values[:3]},
                                70,
                            )
        print(f"   Data extracted: {extracted}")

    async def _run_blockchain(self, target: str) -> None:
        print(f"{Colors.C}[07/18] Blockchain Wallet Hunter...{Colors.END}")
        wallets = await self.blockchain.extract_wallets(target)
        for w in wallets:
            self._add_artifact(
                f"crypto_{w['coin']}", w["file"], w, w["severity"]
            )
        print(f"   Wallets found: {len(wallets)}")

    async def _run_db_forensics(self, target: str) -> None:
        print(f"{Colors.C}[08/18] SQLite Database Analysis...{Colors.END}")
        count = 0
        for root, _, files in os.walk(target):
            for f in files:
                if f.endswith((".db", ".sqlite")):
                    path = os.path.join(root, f)
                    info = await self.db_forensics.analyze_sqlite(path)
                    if info and info.get("suspicious_tables"):
                        self._add_artifact(
                            "suspicious_database", path, info, 80
                        )
                        count += 1
        print(f"   Suspicious DBs: {count}")

    async def _run_zip_crack(self, target: str) -> None:
        print(f"{Colors.C}[09/18] Encrypted Archive Analysis...{Colors.END}")
        for root, _, files in os.walk(target):
            for f in files:
                if f.endswith(".zip"):
                    path = os.path.join(root, f)
                    cracked = await self.crypto.crack_zip(
                        path, output_dir=self.quarantine_dir
                    )
                    if cracked and cracked.get("cracked"):
                        self._add_artifact(
                            "cracked_archive",
                            cracked["file"],
                            cracked,
                            100,
                        )

    async def _run_memory(self) -> None:
        if not IS_ROOT:
            return
        print(f"{Colors.C}[10/18] Memory Forensics...{Colors.END}")
        dump = await self.memory.acquire_memory(
            os.path.join(self.output_dir, "memory_dump.raw")
        )
        if dump:
            findings = await self.memory.analyze_dump(dump)
            for m in findings:
                self._add_artifact("memory_secret", "RAM", m, 95)
            print(f"   Secrets in RAM: {len(findings)}")

    async def _run_behavioral(self) -> None:
        if not PSUTIL_AVAILABLE:
            return
        print(f"{Colors.C}[11/18] Behavioral ML (Process anomalies)...{Colors.END}")
        procs = []
        for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
            try:
                info = p.info
                procs.append({
                    "pid": info["pid"],
                    "name": info["name"],
                    "cpu_percent": info.get("cpu_percent", 0) or 0,
                    "memory_percent": info.get("memory_percent", 0) or 0,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        anomalies = self.ml.detect_anomalies(procs)
        for a in anomalies:
            self._add_artifact("behavioral_anomaly", str(a["pid"]), a, 75)
        print(f"   Anomalies: {len(anomalies)}")

    # ----- artifact management -----

    def _add_artifact(
        self,
        ioc_type: str,
        path: str,
        metadata: Any,
        severity: int,
    ) -> None:
        art = ThreatArtifact(
            ioc_type=ioc_type,
            path=path,
            metadata=metadata if isinstance(metadata, dict) else {"raw": str(metadata)},
            severity=severity,
        )
        self.artifacts.append(art)

        db_path = os.path.join(self.output_dir, "arsenale.db")
        try:
            with sqlite3.connect(db_path) as conn:
                conn.execute(
                    "INSERT OR IGNORE INTO artifacts VALUES (?,?,?,?,?,?)",
                    (
                        art.id,
                        art.timestamp,
                        ioc_type,
                        path,
                        severity,
                        json.dumps(art.metadata, default=str),
                    ),
                )
        except sqlite3.Error as exc:
            logger.warning("DB write failed: %s", exc)

    # ----- reporting -----

    @staticmethod
    def _banner() -> None:
        print(f"{Colors.R}{Colors.BOLD}")
        print("+" + "=" * 58 + "+")
        print("|     PREDATOR HUNT ARSENALE OMNIBUS vFINALE              |")
        print("|     18 Forensic Modules Active                          |")
        print("+" + "=" * 58 + "+")
        print(f"{Colors.END}")

    def _save_and_report(self) -> None:
        critical = [a for a in self.artifacts if a.severity >= 80]
        high = [a for a in self.artifacts if 60 <= a.severity < 80]

        report = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "system": {"root": IS_ROOT, "android": IS_ANDROID},
            "summary": {
                "total": len(self.artifacts),
                "critical": len(critical),
                "high": len(high),
            },
            "findings": [asdict(a) for a in self.artifacts],
        }

        ts = datetime.now(tz=timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_path = os.path.join(
            self.output_dir, f"FINAL_REPORT_{ts}.json"
        )
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        # HTML report
        rows = "\n".join(
            f'<tr class="critical"><td>{c.ioc_type}</td>'
            f"<td>{os.path.basename(c.path)}</td>"
            f"<td>{c.severity}</td></tr>"
            for c in critical[:20]
        )
        html = (
            "<html><head><title>Predator Report</title>\n"
            "<style>\n"
            "body{background:#000;color:#0f0;font-family:monospace;padding:20px}\n"
            ".critical{color:#f00;font-weight:bold}\n"
            ".high{color:orange}\n"
            "table{border-collapse:collapse;width:100%}\n"
            "th,td{border:1px solid #0f0;padding:8px}\n"
            "th{background:#0f0;color:#000}\n"
            "</style></head><body>\n"
            "<h1>PREDATOR HUNT ARSENALE OMNIBUS</h1>\n"
            f"<h2>Total: {len(self.artifacts)} | "
            f"Critical: {len(critical)} | High: {len(high)}</h2>\n"
            "<table>\n"
            "<tr><th>Type</th><th>Path</th><th>Severity</th></tr>\n"
            f"{rows}\n"
            "</table>\n"
            "</body></html>"
        )
        html_path = os.path.join(self.output_dir, "REPORT.html")
        with open(html_path, "w") as f:
            f.write(html)

        print(f"\n{Colors.G}{'=' * 60}{Colors.END}")
        print(f"{Colors.G}SCAN COMPLETE{Colors.END}")
        print(
            f"Total: {len(self.artifacts)} | "
            f"{Colors.R}Critical: {len(critical)}{Colors.END} | "
            f"{Colors.Y}High: {len(high)}{Colors.END}"
        )
        print(f"Report JSON: {report_path}")
        print(f"Report HTML: {html_path}")
        print(f"{Colors.G}{'=' * 60}{Colors.END}")


# ===========================================================================
# CLI ENTRY POINT
# ===========================================================================

def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser."""
    parser = argparse.ArgumentParser(
        description="Predator Hunt - Arsenale Omnibus",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  %(prog)s /sdcard/Download\n"
            "  %(prog)s --apk app.apk --pcap capture.pcap /sdcard\n"
        ),
    )
    parser.add_argument(
        "target",
        nargs="?",
        default="/sdcard/Download",
        help="Target path to analyse (default: /sdcard/Download)",
    )
    parser.add_argument(
        "--apk",
        action="append",
        default=[],
        metavar="FILE",
        help="Specific APK file(s) to analyse (repeatable).",
    )
    parser.add_argument(
        "--pcap",
        action="append",
        default=[],
        metavar="FILE",
        help="PCAP file(s) to analyse (repeatable).",
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        metavar="DIR",
        help="Output directory for reports (default: ~/PredatorHunt).",
    )
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """
    CLI entry point.

    Args:
        argv: Command-line arguments.

    Returns:
        Exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    hunter = PredatorHunt(output_dir=args.output_dir)
    asyncio.run(hunter.scan(args.target))
    return 0


if __name__ == "__main__":
    sys.exit(main())
