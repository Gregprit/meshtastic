import threading
import time
from typing import Callable, Optional

from meshtastic import serial_interface, tcp_interface
from pubsub import pub


def chunk_text(text: str, max_len: int = 190) -> list[str]:
    chunks = []
    remaining = text
    while remaining:
        chunk = remaining[:max_len]
        chunks.append(chunk)
        remaining = remaining[max_len:]
    return chunks


def parse_sender(packet: dict) -> Optional[str]:
    if not packet:
        return None
    from_id = packet.get("fromId") or packet.get("from")
    if isinstance(from_id, str):
        return from_id
    return None


def parse_channel(packet: dict) -> Optional[int]:
    if not packet:
        return None
    return packet.get("channel")


def parse_text(packet: dict) -> Optional[str]:
    if not packet:
        return None
    payload = packet.get("decoded") or {}
    return payload.get("text")


class MeshtasticClient:
    def __init__(
        self,
        serial_path: Optional[str],
        host: Optional[str],
        port: Optional[int],
        alert_channel_index: int,
        on_text: Callable[[str, Optional[int], Optional[str]], None],
    ) -> None:
        self.serial_path = serial_path
        self.host = host
        self.port = port
        self.alert_channel_index = alert_channel_index
        self.on_text = on_text
        self.interface = None

    def connect(self) -> None:
        if self.serial_path:
            self.interface = serial_interface.SerialInterface(self.serial_path)
        else:
            host = self.host or "localhost"
            port = self.port or 4403
            self.interface = tcp_interface.TCPInterface(hostname=host, port=port)
        pub.subscribe(self._handle_receive, "meshtastic.receive")

    def _handle_receive(self, packet: dict) -> None:
        text = parse_text(packet)
        if not text:
            return
        channel = parse_channel(packet)
        sender = parse_sender(packet)
        self.on_text(text, channel, sender)

    def send_channel(self, text: str) -> None:
        if not self.interface:
            return
        self.interface.sendText(text, channelIndex=self.alert_channel_index)

    def send_dm(self, text: str, destination: str) -> None:
        if not self.interface:
            return
        self.interface.sendText(text, destinationId=destination)

    def send_chunked(self, text: str, destination: str, delay_s: float = 1.2) -> None:
        chunks = chunk_text(text)
        for chunk in chunks:
            self.send_dm(chunk, destination)
            time.sleep(delay_s)

    def send_chunked_channel(self, text: str, delay_s: float = 1.2) -> None:
        chunks = chunk_text(text)
        for chunk in chunks:
            self.send_channel(chunk)
            time.sleep(delay_s)

    def start(self) -> None:
        thread = threading.Thread(target=self.connect, daemon=True)
        thread.start()
