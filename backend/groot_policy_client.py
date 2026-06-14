from __future__ import annotations

import functools
from typing import Any

import msgpack
import msgpack_numpy as mnp
import zmq


class MsgSerializer:
    @staticmethod
    def to_bytes(data: Any) -> bytes:
        default = functools.partial(MsgSerializer._safe_encode, chain=MsgSerializer._encode_custom)
        return msgpack.packb(data, default=default)

    @staticmethod
    def from_bytes(data: bytes) -> Any:
        object_hook = functools.partial(
            MsgSerializer._safe_decode,
            chain=MsgSerializer._decode_custom,
        )
        return msgpack.unpackb(data, object_hook=object_hook, raw=False)

    @staticmethod
    def _safe_encode(obj: Any, chain=None) -> Any:
        return mnp.encode(obj, chain=chain)

    @staticmethod
    def _safe_decode(obj: Any, chain=None) -> Any:
        return mnp.decode(obj, chain=chain)

    @staticmethod
    def _encode_custom(obj: Any) -> Any:
        return obj

    @staticmethod
    def _decode_custom(obj: Any) -> Any:
        if not isinstance(obj, dict):
            return obj

        if "__ModalityConfig__" in obj and "as_json" in obj:
            return obj["as_json"]
        if b"__ModalityConfig__" in obj and b"as_json" in obj:
            return obj[b"as_json"]
        return obj


class PolicyClient:
    def __init__(
        self,
        host: str,
        port: int,
        timeout_ms: int = 15000,
        api_token: str | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.timeout_ms = timeout_ms
        self.api_token = api_token
        self.context = zmq.Context()
        self._init_socket()

    def _init_socket(self) -> None:
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.RCVTIMEO, self.timeout_ms)
        self.socket.setsockopt(zmq.SNDTIMEO, self.timeout_ms)
        self.socket.connect(f"tcp://{self.host}:{self.port}")

    def close(self) -> None:
        self.socket.close()
        self.context.term()

    def call_endpoint(
        self,
        endpoint: str,
        data: dict[str, Any] | None = None,
        requires_input: bool = True,
    ) -> Any:
        request: dict[str, Any] = {"endpoint": endpoint}
        if requires_input:
            request["data"] = data or {}
        if self.api_token:
            request["api_token"] = self.api_token

        try:
            self.socket.send(MsgSerializer.to_bytes(request))
            message = self.socket.recv()
        except zmq.error.Again as exc:
            self._init_socket()
            raise TimeoutError(
                f"GROOT policy server timeout at tcp://{self.host}:{self.port}"
            ) from exc

        response = MsgSerializer.from_bytes(message)
        if isinstance(response, dict) and "error" in response:
            raise RuntimeError(f"Server error: {response['error']}")
        return response

    def ping(self) -> bool:
        try:
            self.call_endpoint("ping", requires_input=False)
            return True
        except Exception:
            return False

    def get_modality_config(self) -> dict[str, dict[str, Any]]:
        response = self.call_endpoint("get_modality_config", requires_input=False)
        if not isinstance(response, dict):
            raise RuntimeError(f"Unexpected modality config response: {type(response)!r}")
        return response

    def get_action(
        self,
        observation: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        response = self.call_endpoint(
            "get_action",
            {"observation": observation, "options": options},
        )
        if not isinstance(response, (list, tuple)) or len(response) != 2:
            raise RuntimeError(f"Unexpected get_action response: {response!r}")
        action, info = response
        if not isinstance(action, dict) or not isinstance(info, dict):
            raise RuntimeError(f"Unexpected get_action payload: {response!r}")
        return action, info
