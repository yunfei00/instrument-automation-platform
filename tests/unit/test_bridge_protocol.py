import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "packages" / "instrument_core" / "src"))

from instrument_core.bridge.models import TcpBridgeConfig, VisaBridgeConfig
from instrument_core.bridge.protocol import ScpiLineFramer, is_scpi_query


def test_scpi_line_framer_handles_split_tcp_packets():
    framer = ScpiLineFramer()

    assert framer.feed(b"*ID") == []
    assert framer.feed(b"N?\n:RUN\nPART") == [b"*IDN?\n", b":RUN\n"]
    assert framer.pending_bytes == 4
    assert framer.feed(b"IAL\n") == [b"PARTIAL\n"]
    assert framer.pending_bytes == 0


def test_query_detection_ignores_binary_payload_question_mark():
    assert is_scpi_query(b"*IDN?\n") is True
    assert is_scpi_query(b":WAV:DATA?\n") is True
    assert is_scpi_query(b":RUN\n") is False
    assert is_scpi_query(b":DATA #13a?b\n") is False


def test_tcp_bridge_config_validates_ports():
    config = TcpBridgeConfig(remote_host="192.0.2.10", remote_port=5025)
    config.validate()

    with pytest.raises(ValueError):
        TcpBridgeConfig(remote_host="x", remote_port=70000).validate()


def test_visa_bridge_config_requires_resource():
    with pytest.raises(ValueError):
        VisaBridgeConfig(resource="").validate()
