from django.contrib import admin
from .models import (
    Institution, InstitutionMember,
    Batch, BatchStaff, BatchInvite,
    Enrollment,
    CoursePack, CoursePackItem,
    Assignment, AssignmentItem,
    Submission, SubmissionAttempt,
    Grade, RegradeRequest,
    Rubric, RubricCriterion, RubricScore,
    Certificate, AuditLog,
    ParentLink,
)

admin.site.register(Institution)
admin.site.register(InstitutionMember)
admin.site.register(Batch)
admin.site.register(BatchStaff)
admin.site.register(BatchInvite)
admin.site.register(Enrollment)
admin.site.register(CoursePack)
admin.site.register(CoursePackItem)
admin.site.register(Assignment)
admin.site.register(AssignmentItem)
admin.site.register(Submission)
admin.site.register(SubmissionAttempt)
admin.site.register(Grade)
admin.site.register(RegradeRequest)
admin.site.register(Rubric)
admin.site.register(RubricCriterion)
admin.site.register(RubricScore)
admin.site.register(Certificate)
admin.site.register(AuditLog)
admin.site.register(ParentLink)
