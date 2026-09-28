"""Run with: python -m unittest tests.test_feedback"""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app


class FeedbackTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = patch("app.services.feedback._FILE", Path(self.tmp.name) / "sugestoes.jsonl")
        patcher.start()
        self.addCleanup(patcher.stop)
        self.client = TestClient(app)

    def test_blank_message_is_rejected(self):
        r = self.client.post("/api/feedback", json={"mensagem": "   "})
        self.assertEqual(r.status_code, 422)

    def test_message_is_saved_and_readable(self):
        r = self.client.post("/api/feedback", json={"mensagem": "Mais ligas, por favor", "contacto": "a@b.com"})
        self.assertEqual(r.status_code, 200)
        from app.services import feedback

        saved = feedback.read_suggestions()
        self.assertEqual(len(saved), 1)
        self.assertEqual(saved[0]["mensagem"], "Mais ligas, por favor")
        self.assertEqual(saved[0]["contacto"], "a@b.com")

    def test_contacto_is_optional(self):
        r = self.client.post("/api/feedback", json={"mensagem": "Só uma ideia"})
        self.assertEqual(r.status_code, 200)
