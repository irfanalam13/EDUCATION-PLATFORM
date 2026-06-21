"""Phase 2b authorization regression tests for the content app (IDOR fixes)."""
from __future__ import annotations

from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase

from apps.academics.models import Level, Subject, Chapter, Topic, Tag
from apps.content.models import Note, NoteTag

User = get_user_model()


class ContentAuthzTest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.alice = User.objects.create_user(username="alice", email="a@x.com", password="pw-1234aa")
        cls.bob = User.objects.create_user(username="bob", email="b@x.com", password="pw-1234bb")
        cls.level = Level.objects.create(name="Grade 10")
        cls.subject = Subject.objects.create(level=cls.level, name="Math")
        cls.chapter = Chapter.objects.create(subject=cls.subject, title="Ch", number=1)
        cls.topic = Topic.objects.create(chapter=cls.chapter, title="T")

    # ---- Collections: IDOR on update/delete ----
    def test_user_cannot_edit_others_collection(self):
        self.client.force_authenticate(self.alice)
        resp = self.client.post(
            "/api/content/collections/",
            {"topic": self.topic.id, "title": "Alice's", "is_published": True},
            format="json",
        )
        self.assertEqual(resp.status_code, 201, resp.content)
        cid = resp.data["id"]

        # Bob can READ a published collection but cannot edit or delete it.
        self.client.force_authenticate(self.bob)
        patch = self.client.patch(f"/api/content/collections/{cid}/", {"title": "hacked"}, format="json")
        self.assertEqual(patch.status_code, 403)
        delete = self.client.delete(f"/api/content/collections/{cid}/")
        self.assertEqual(delete.status_code, 403)

        # Owner can edit.
        self.client.force_authenticate(self.alice)
        ok = self.client.patch(f"/api/content/collections/{cid}/", {"title": "renamed"}, format="json")
        self.assertEqual(ok.status_code, 200)

    # ---- Notes: private notes must not leak in list ----
    def test_private_notes_not_listed_to_others(self):
        Note.objects.create(
            topic=self.topic, title="secret", content_richtext="x",
            visibility="private", created_by=self.alice,
        )
        Note.objects.create(
            topic=self.topic, title="public", content_richtext="y",
            visibility="public", created_by=self.alice,
        )
        self.client.force_authenticate(self.bob)
        resp = self.client.get("/api/content/notes/?visibility=private")
        results = resp.data["results"] if isinstance(resp.data, dict) else resp.data
        titles = [n["title"] for n in results]
        self.assertNotIn("secret", titles)

    # ---- NoteTag: only the note's owner may detach tags ----
    def test_user_cannot_delete_tag_on_others_note(self):
        note = Note.objects.create(
            topic=self.topic, title="n", content_richtext="z",
            visibility="public", created_by=self.alice,
        )
        tag = Tag.objects.create(name="algebra")
        nt = NoteTag.objects.create(note=note, tag=tag)

        self.client.force_authenticate(self.bob)
        resp = self.client.delete(f"/api/content/note-tags/{nt.id}/")
        self.assertEqual(resp.status_code, 403)
