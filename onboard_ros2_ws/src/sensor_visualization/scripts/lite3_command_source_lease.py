#!/usr/bin/env python3
"""Shared fail-closed LAPTOP_XBOX lease; the only manual source writer."""

from __future__ import annotations

import fcntl
import json
import os
from pathlib import Path


class LaptopXboxLease:
    """Own the existing command-source flock and marker as one transaction."""

    def __init__(self, state_dir):
        self.state_dir = Path(state_dir)
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.source_path = self.state_dir / "COMMAND_SOURCE"
        self.lock_path = self.state_dir / "owner.lock"
        self.remote_owner_path = self.state_dir / "NOMAD_REMOTE_OWNER.json"
        self.lock = None

    @staticmethod
    def _validated_owner(owner):
        if owner is None:
            return None
        required = {"authority_id", "control_epoch", "lease_generation", "session_id"}
        if not isinstance(owner, dict) or set(owner) != required:
            raise ValueError("remote owner metadata is invalid")
        if not all(isinstance(owner[key], str) and owner[key] for key in
                   ("authority_id", "session_id")):
            raise ValueError("remote owner identity is invalid")
        if any(type(owner[key]) is not int or owner[key] < 0 for key in
               ("control_epoch", "lease_generation")):
            raise ValueError("remote owner generation is invalid")
        return dict(owner)

    def _write_owner(self, owner):
        owner = self._validated_owner(owner)
        if owner is None:
            self._clear_owner()
            return
        temp = self.remote_owner_path.with_name(
            f".{self.remote_owner_path.name}.{os.getpid()}")
        temp.write_text(json.dumps(owner, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temp, self.remote_owner_path)

    def _clear_owner(self):
        try:
            self.remote_owner_path.unlink()
        except FileNotFoundError:
            pass

    def acquire(self, remote_owner=None):
        if self.lock is not None:
            return True
        lock = self.lock_path.open("a+")
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock.close()
            return False
        current = (self.source_path.read_text(encoding="utf-8").strip()
                   if self.source_path.exists() else "NONE")
        if current != "NONE":
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()
            return False
        try:
            self._write_owner(remote_owner)
            self.source_path.write_text("LAPTOP_XBOX\n", encoding="utf-8")
        except Exception:
            self._clear_owner()
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()
            raise
        self.lock = lock
        return True

    def recover_stale_own_marker(self):
        if self.lock is not None:
            return False
        lock = self.lock_path.open("a+")
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            lock.close()
            return False
        try:
            if self.owner() != "LAPTOP_XBOX":
                return False
            self.source_path.write_text("NONE\n", encoding="utf-8")
            self._clear_owner()
            return True
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)
            lock.close()

    def release(self):
        if self.lock is None:
            return
        current = (self.source_path.read_text(encoding="utf-8").strip()
                   if self.source_path.exists() else "NONE")
        if current == "LAPTOP_XBOX":
            self.source_path.write_text("NONE\n", encoding="utf-8")
        self._clear_owner()
        fcntl.flock(self.lock.fileno(), fcntl.LOCK_UN)
        self.lock.close()
        self.lock = None

    def owner(self):
        return (self.source_path.read_text(encoding="utf-8").strip()
                if self.source_path.exists() else "NONE")

    def remote_owner(self):
        try:
            value = json.loads(self.remote_owner_path.read_text(encoding="utf-8"))
            return self._validated_owner(value)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            return None
