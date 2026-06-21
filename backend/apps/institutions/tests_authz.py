"""Phase 2b regression tests: institutions object-level authorization.

Covers the grade-tampering fix — authorization must resolve the batch from the
object (submission/assignment), not from the URL pk.
"""
from __future__ import annotations

from types import SimpleNamespace

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.institutions.models import Institution, Batch, BatchStaff
from apps.institutions.permissions import IsBatchStaffForObject, _resolve_batch_id

User = get_user_model()


class BatchObjectPermissionTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.inst = Institution.objects.create(name="Inst", slug="inst")
        cls.batch = Batch.objects.create(institution=cls.inst, name="B1")
        cls.other_batch = Batch.objects.create(institution=cls.inst, name="B2")
        cls.teacher = User.objects.create_user(username="teach", email="te@x.com", password="pw-1234aa")
        cls.stranger = User.objects.create_user(username="str", email="st@x.com", password="pw-1234aa")
        BatchStaff.objects.create(batch=cls.batch, user=cls.teacher, role=BatchStaff.Role.TEACHER)

    def test_resolve_batch_id_from_assignment_chain(self):
        # Submission-like object: obj.assignment.batch_id
        sub = SimpleNamespace(assignment=SimpleNamespace(batch_id=self.batch.id), batch_id=None)
        self.assertEqual(_resolve_batch_id(sub), self.batch.id)
        # Assignment-like object: obj.batch_id
        assignment = SimpleNamespace(batch_id=self.batch.id)
        self.assertEqual(_resolve_batch_id(assignment), self.batch.id)

    def _check(self, user, method, obj):
        perm = IsBatchStaffForObject()
        req = SimpleNamespace(user=user, method=method)
        return perm.has_object_permission(req, None, obj)

    def test_teacher_of_batch_can_write(self):
        sub = SimpleNamespace(assignment=SimpleNamespace(batch_id=self.batch.id), batch_id=None)
        self.assertTrue(self._check(self.teacher, "POST", sub))

    def test_non_teacher_cannot_write(self):
        sub = SimpleNamespace(assignment=SimpleNamespace(batch_id=self.batch.id), batch_id=None)
        self.assertFalse(self._check(self.stranger, "POST", sub))

    def test_teacher_of_other_batch_cannot_grade_this_submission(self):
        # The exact grade-tampering scenario: teacher of other_batch, submission in batch.
        BatchStaff.objects.create(batch=self.other_batch, user=self.stranger, role=BatchStaff.Role.TEACHER)
        sub = SimpleNamespace(assignment=SimpleNamespace(batch_id=self.batch.id), batch_id=None)
        self.assertFalse(self._check(self.stranger, "POST", sub))

    def test_reads_allowed_for_anyone(self):
        sub = SimpleNamespace(assignment=SimpleNamespace(batch_id=self.batch.id), batch_id=None)
        self.assertTrue(self._check(self.stranger, "GET", sub))
