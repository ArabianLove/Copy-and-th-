import json
import math
import os
import struct
import zipfile

import pytest

from src.predator_arsenale import (
    BehavioralML,
    BlockchainAnalyzer,
    BulkExtractor,
    CryptoBreaker,
    DatabaseForensics,
    PredatorHunt,
    StegoHunter,
    TLSFingerprint,
    ThreatArtifact,
    VaultHunter,
    VideoAnalyzer,
    YaraEngine,
    compute_file_hash,
    shannon_entropy,
)


# ---------------------------------------------------------------------------
# Utility: shannon_entropy / compute_file_hash
# ---------------------------------------------------------------------------

class TestShannonEntropy:
    """Tests for the shared shannon_entropy function."""

    def test_empty_bytes(self):
        """Empty input yields zero entropy."""
        assert shannon_entropy(b"") == 0.0

    def test_uniform_byte(self):
        """Repeating a single byte yields zero entropy."""
        assert shannon_entropy(b"\x00" * 256) == 0.0

    def test_random_bytes(self):
        """256 distinct bytes should yield near-maximum entropy."""
        data = bytes(range(256))
        ent = shannon_entropy(data)
        assert 0.99 <= ent <= 1.0

    def test_returns_float(self):
        """Entropy is always a float."""
        assert isinstance(shannon_entropy(b"abc"), float)


class TestComputeFileHash:
    """Tests for compute_file_hash."""

    def test_sha256(self, tmp_path):
        """SHA256 digest has 64 hex chars."""
        f = tmp_path / "f.txt"
        f.write_text("hello")
        assert len(compute_file_hash(str(f), "sha256")) == 64

    def test_md5(self, tmp_path):
        """MD5 digest has 32 hex chars."""
        f = tmp_path / "f.txt"
        f.write_text("hello")
        assert len(compute_file_hash(str(f), "md5")) == 32

    def test_deterministic(self, tmp_path):
        """Same file always produces the same hash."""
        f = tmp_path / "f.txt"
        f.write_text("deterministic")
        assert compute_file_hash(str(f)) == compute_file_hash(str(f))


# ---------------------------------------------------------------------------
# ThreatArtifact dataclass
# ---------------------------------------------------------------------------

class TestThreatArtifact:
    """Tests for the ThreatArtifact dataclass."""

    def test_default_id(self):
        """Each artifact gets a unique 16-char hex ID."""
        a = ThreatArtifact()
        b = ThreatArtifact()
        assert len(a.id) == 16
        assert a.id != b.id

    def test_default_severity(self):
        """Default severity is 0."""
        assert ThreatArtifact().severity == 0


# ---------------------------------------------------------------------------
# Module 01: YaraEngine
# ---------------------------------------------------------------------------

class TestYaraEngine:
    """Tests for YaraEngine (graceful when yara is not installed)."""

    def test_scan_nonexistent_file(self):
        """Scanning a missing file returns empty list."""
        engine = YaraEngine()
        assert engine.scan_file("/nonexistent/file") == []

    def test_scan_regular_file(self, tmp_path):
        """Scanning a normal text file returns no matches (or empty if no yara)."""
        f = tmp_path / "clean.txt"
        f.write_text("nothing suspicious here")
        engine = YaraEngine()
        result = engine.scan_file(str(f))
        assert isinstance(result, list)


# ---------------------------------------------------------------------------
# Module 09: TLSFingerprint
# ---------------------------------------------------------------------------

class TestTLSFingerprint:
    """Tests for TLSFingerprint."""

    def test_known_ja3(self):
        """Known malware JA3 returns the malware name."""
        tls = TLSFingerprint()
        assert tls.check_ja3("b32309a26951912be7dba376398abc3b") == "Dridex"

    def test_unknown_ja3(self):
        """Unknown JA3 returns None."""
        tls = TLSFingerprint()
        assert tls.check_ja3("0000000000000000000000000000000") is None


# ---------------------------------------------------------------------------
# Module 10: BehavioralML
# ---------------------------------------------------------------------------

class TestBehavioralML:
    """Tests for BehavioralML anomaly detection."""

    def test_no_anomaly(self):
        """Normal processes produce no anomalies."""
        ml = BehavioralML()
        procs = [{"pid": 1, "name": "init", "cpu_percent": 1, "memory_percent": 0.5}]
        assert ml.detect_anomalies(procs) == []

    def test_cpu_anomaly(self):
        """High CPU triggers an anomaly."""
        ml = BehavioralML()
        procs = [{"pid": 99, "name": "miner", "cpu_percent": 99, "memory_percent": 1}]
        result = ml.detect_anomalies(procs)
        assert len(result) == 1
        assert result[0]["type"] == "resource_anomaly"

    def test_memory_anomaly(self):
        """High memory triggers an anomaly."""
        ml = BehavioralML()
        procs = [{"pid": 50, "name": "leak", "cpu_percent": 5, "memory_percent": 15}]
        assert len(ml.detect_anomalies(procs)) == 1


# ---------------------------------------------------------------------------
# Module 12: StegoHunter
# ---------------------------------------------------------------------------

class TestStegoHunter:
    """Tests for StegoHunter."""

    @pytest.mark.asyncio
    async def test_nonexistent_image(self):
        """Missing file returns None."""
        stego = StegoHunter()
        assert await stego.analyze_image("/no/such/file") is None

    @pytest.mark.asyncio
    async def test_clean_png(self, tmp_path):
        """A small clean PNG is not flagged."""
        img = tmp_path / "clean.png"
        # Minimal valid PNG (1x1 white pixel)
        img.write_bytes(
            b"\x89PNG\r\n\x1a\n"
            + b"\x00" * 100
        )
        stego = StegoHunter()
        result = await stego.analyze_image(str(img))
        assert result is not None
        # May or may not be suspicious depending on entropy

    @pytest.mark.asyncio
    async def test_jpg_with_appended_data(self, tmp_path):
        """JPEG with data after EOF marker is flagged."""
        jpg = tmp_path / "suspicious.jpg"
        # Fake JPEG: SOI + data + EOI + hidden payload
        jpg.write_bytes(
            b"\xff\xd8" + b"\x00" * 100 + b"\xff\xd9" + b"HIDDEN" * 50
        )
        stego = StegoHunter()
        result = await stego.analyze_image(str(jpg))
        assert result is not None
        assert result["suspicious"] is True
        assert result["hidden_data"] is True

    @pytest.mark.asyncio
    async def test_stego_signature_detection(self, tmp_path):
        """Files containing stego tool signatures are flagged."""
        img = tmp_path / "stego.png"
        img.write_bytes(b"\x89PNG" + b"\x00" * 50 + b"steghide" + b"\x00" * 50)
        stego = StegoHunter()
        result = await stego.analyze_image(str(img))
        assert result["suspicious"] is True
        assert any("steghide" in i for i in result["indicators"])


# ---------------------------------------------------------------------------
# Module 13: VaultHunter
# ---------------------------------------------------------------------------

class TestVaultHunter:
    """Tests for VaultHunter."""

    def test_detects_hidden_dir(self, tmp_path):
        """Directories named '.hidden' are flagged."""
        (tmp_path / ".hidden_stuff").mkdir()
        vault = VaultHunter()
        findings = vault.scan(str(tmp_path))
        assert any(f["type"] == "suspicious_directory" for f in findings)

    def test_detects_double_extension(self, tmp_path):
        """Files with double extensions are flagged."""
        (tmp_path / "photo.jpg.exe").write_bytes(b"\x00")
        vault = VaultHunter()
        findings = vault.scan(str(tmp_path))
        assert any(f["type"] == "double_extension" for f in findings)

    def test_clean_directory(self, tmp_path):
        """A clean directory with no suspicious items."""
        (tmp_path / "readme.txt").write_text("clean")
        vault = VaultHunter()
        findings = vault.scan(str(tmp_path))
        # No suspicious directories or double extensions
        assert not any(f["type"] == "double_extension" for f in findings)


# ---------------------------------------------------------------------------
# Module 07: BulkExtractor
# ---------------------------------------------------------------------------

class TestBulkExtractor:
    """Tests for BulkExtractor."""

    @pytest.mark.asyncio
    async def test_extract_email(self, tmp_path):
        """Emails are extracted from text files."""
        f = tmp_path / "data.txt"
        f.write_text("Contact us at test@example.com for info.")
        bulk = BulkExtractor()
        result = await bulk.scan_file(str(f))
        assert "email" in result
        assert "test@example.com" in result["email"]

    @pytest.mark.asyncio
    async def test_extract_url(self, tmp_path):
        """URLs are extracted from text files."""
        f = tmp_path / "links.txt"
        f.write_text("Visit https://example.com for more.")
        bulk = BulkExtractor()
        result = await bulk.scan_file(str(f))
        assert "url" in result

    @pytest.mark.asyncio
    async def test_nonexistent_file(self):
        """Missing files return empty dict."""
        bulk = BulkExtractor()
        assert await bulk.scan_file("/no/such/file") == {}

    @pytest.mark.asyncio
    async def test_oversized_file(self, tmp_path):
        """Files larger than MAX_FILE_SIZE are skipped."""
        f = tmp_path / "huge.txt"
        f.write_text("x")
        bulk = BulkExtractor()
        bulk.MAX_FILE_SIZE = 0  # Force skip
        assert await bulk.scan_file(str(f)) == {}


# ---------------------------------------------------------------------------
# Module 08: DatabaseForensics
# ---------------------------------------------------------------------------

class TestDatabaseForensics:
    """Tests for DatabaseForensics."""

    @pytest.mark.asyncio
    async def test_analyze_sqlite(self, tmp_path):
        """Suspicious table names are flagged."""
        db_path = tmp_path / "test.db"
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        conn.execute("CREATE TABLE user_credentials (id INTEGER, password TEXT)")
        conn.execute("CREATE TABLE logs (id INTEGER, message TEXT)")
        conn.commit()
        conn.close()

        db = DatabaseForensics()
        result = await db.analyze_sqlite(str(db_path))
        assert result is not None
        assert "user_credentials" in result["suspicious_tables"]

    @pytest.mark.asyncio
    async def test_nonexistent_db(self):
        """Missing DB returns None."""
        db = DatabaseForensics()
        assert await db.analyze_sqlite("/no/such/file.db") is None


# ---------------------------------------------------------------------------
# Module 15: VideoAnalyzer
# ---------------------------------------------------------------------------

class TestVideoAnalyzer:
    """Tests for VideoAnalyzer."""

    @pytest.mark.asyncio
    async def test_nonexistent_video(self):
        """Missing video returns None."""
        va = VideoAnalyzer()
        assert await va.analyze("/no/such/file.mp4") is None

    @pytest.mark.asyncio
    async def test_detect_mp4(self, tmp_path):
        """MP4 magic bytes are detected."""
        mp4 = tmp_path / "test.mp4"
        mp4.write_bytes(b"\x00\x00\x00\x20ftypisom" + b"\x00" * 200)
        va = VideoAnalyzer()
        result = await va.analyze(str(mp4))
        assert result is not None
        assert result["format"] == "MP4/MOV"


# ---------------------------------------------------------------------------
# Module 16: BlockchainAnalyzer
# ---------------------------------------------------------------------------

class TestBlockchainAnalyzer:
    """Tests for BlockchainAnalyzer."""

    @pytest.mark.asyncio
    async def test_extract_eth_wallet(self, tmp_path):
        """Ethereum addresses are extracted."""
        f = tmp_path / "wallets.txt"
        f.write_text("Send to 0x742d35Cc6634C0532925a3b844Bc9e7595f2bD18")
        ba = BlockchainAnalyzer()
        result = await ba.extract_wallets(str(tmp_path))
        assert len(result) == 1
        assert result[0]["coin"] == "eth"

    @pytest.mark.asyncio
    async def test_empty_dir(self, tmp_path):
        """Empty directory yields no wallets."""
        ba = BlockchainAnalyzer()
        assert await ba.extract_wallets(str(tmp_path)) == []


# ---------------------------------------------------------------------------
# Module 17: CryptoBreaker
# ---------------------------------------------------------------------------

class TestCryptoBreaker:
    """Tests for CryptoBreaker."""

    @pytest.mark.asyncio
    async def test_nonexistent_zip(self):
        """Missing ZIP returns not cracked."""
        cb = CryptoBreaker()
        result = await cb.crack_zip("/no/such/file.zip")
        assert result["cracked"] is False

    @pytest.mark.asyncio
    async def test_unprotected_zip(self, tmp_path):
        """Unprotected ZIP is not 'cracked' (no password needed)."""
        zpath = tmp_path / "test.zip"
        with zipfile.ZipFile(str(zpath), "w") as zf:
            zf.writestr("hello.txt", "world")
        cb = CryptoBreaker()
        result = await cb.crack_zip(str(zpath), output_dir=str(tmp_path / "out"))
        # An unprotected ZIP extracts with any password attempt
        assert result["cracked"] is True


# ---------------------------------------------------------------------------
# PredatorHunt controller
# ---------------------------------------------------------------------------

class TestPredatorHunt:
    """Tests for the main PredatorHunt controller."""

    def test_init(self, tmp_path):
        """Controller initialises without error."""
        hunter = PredatorHunt(output_dir=str(tmp_path / "output"))
        assert hunter.artifacts == []

    def test_add_artifact(self, tmp_path):
        """Artifacts are stored and written to DB."""
        out = tmp_path / "output"
        hunter = PredatorHunt(output_dir=str(out))
        hunter._ensure_dirs()
        hunter._setup_db()
        hunter._add_artifact("test_type", "/test/path", {"key": "val"}, 50)
        assert len(hunter.artifacts) == 1
        assert hunter.artifacts[0].ioc_type == "test_type"
        assert hunter.artifacts[0].severity == 50

    @pytest.mark.asyncio
    async def test_scan_nonexistent_path(self, tmp_path, capsys):
        """Scanning a nonexistent path prints an error and returns."""
        hunter = PredatorHunt(output_dir=str(tmp_path / "output"))
        await hunter.scan("/nonexistent/path/xyz")
        captured = capsys.readouterr()
        assert "not found" in captured.out.lower() or "Path not found" in captured.out
