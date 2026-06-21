from rest_framework import serializers

from apps.assessment.models import MCQQuestion, MCQOption, PracticeQuestion, QuestionReport
from apps.assessment.models.bank import QuestionType


class MCQOptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MCQOption
        fields = ["id", "text"]


class MCQOptionWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = MCQOption
        fields = ["text", "is_correct"]


class MCQQuestionSerializer(serializers.ModelSerializer):
    options = MCQOptionSerializer(many=True, read_only=True)

    class Meta:
        model = MCQQuestion
        fields = [
            "id",
            "title",
            "question_text",
            "subject",
            "chapter",
            "topic",
            "difficulty",
            "explanation",
            "is_active",
            "options",
            "created_at",
            "updated_at",
        ]


class MCQPlayOptionSerializer(serializers.ModelSerializer):
    # Exposed as `choice_text` to match the quiz clients (web + mobile).
    choice_text = serializers.CharField(source="text", read_only=True)

    class Meta:
        model = MCQOption
        fields = ["id", "choice_text"]


class MCQQuestionPlaySerializer(serializers.ModelSerializer):
    """Student-facing question: no is_correct, no explanation."""
    choices = MCQPlayOptionSerializer(source="options", many=True, read_only=True)

    class Meta:
        model = MCQQuestion
        fields = ["id", "topic", "question_text", "difficulty", "choices"]


class MCQQuestionCreateSerializer(serializers.ModelSerializer):
    options = MCQOptionWriteSerializer(many=True)

    class Meta:
        model = MCQQuestion
        fields = [
            "id",
            "title",
            "question_text",
            "subject",
            "chapter",
            "topic",
            "difficulty",
            "explanation",
            "is_active",
            "options",
        ]

    def validate_options(self, options):
        if not options or len(options) < 2:
            raise serializers.ValidationError("At least 2 options are required.")
        correct_count = sum(1 for o in options if o.get("is_correct") is True)
        if correct_count != 1:
            raise serializers.ValidationError("Exactly 1 option must be marked as correct.")
        return options

    def create(self, validated_data):
        options_data = validated_data.pop("options")
        user = self.context["request"].user if "request" in self.context else None
        q = MCQQuestion.objects.create(created_by=user, **validated_data)
        MCQOption.objects.bulk_create([MCQOption(question=q, **opt) for opt in options_data])
        return q

    def update(self, instance, validated_data):
        options_data = validated_data.pop("options", None)

        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()

        if options_data is not None:
            correct_count = sum(1 for o in options_data if o.get("is_correct") is True)
            if correct_count != 1:
                raise serializers.ValidationError({"options": "Exactly 1 option must be marked as correct."})

            instance.options.all().delete()
            MCQOption.objects.bulk_create([MCQOption(question=instance, **opt) for opt in options_data])

        return instance


class PracticeQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeQuestion
        fields = [
            "id",
            "prompt",
            "answer_text",
            "explanation",
            "subject",
            "chapter",
            "topic",
            "difficulty",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def to_representation(self, instance):
        # The model answer must never reach students. Only staff see answer_text.
        data = super().to_representation(instance)
        request = self.context.get("request")
        user = getattr(request, "user", None)
        if not (user and user.is_staff):
            data.pop("answer_text", None)
        return data


class PracticeQuestionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeQuestion
        fields = [
            "id",
            "prompt",
            "answer_text",
            "explanation",
            "subject",
            "chapter",
            "topic",
            "difficulty",
            "is_active",
        ]

    def create(self, validated_data):
        user = self.context["request"].user if "request" in self.context else None
        return PracticeQuestion.objects.create(created_by=user, **validated_data)


class MCQGenerateInputSerializer(serializers.Serializer):
    """Input for the AI MCQ generation endpoint (mirrors generate_mcqs kwargs)."""
    topic = serializers.CharField(max_length=200)
    count = serializers.IntegerField(min_value=1, max_value=20, default=5)
    difficulty = serializers.ChoiceField(
        choices=["EASY", "MEDIUM", "HARD"], default="MEDIUM"
    )
    grade_level = serializers.CharField(max_length=50, required=False, allow_blank=True, default="")
    language = serializers.CharField(max_length=20, required=False, default="en")


class QuestionReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionReport
        fields = [
            "id",
            "question_type",
            "mcq_question",
            "practice_question",
            "reason",
            "details",
            "status",
            "created_at",
        ]
        read_only_fields = ["status", "created_at"]

    def validate(self, attrs):
        qtype = attrs.get("question_type")
        mcq = attrs.get("mcq_question")
        practice = attrs.get("practice_question")

        if qtype == QuestionType.MCQ and not mcq:
            raise serializers.ValidationError("mcq_question is required when question_type=MCQ.")
        if qtype == QuestionType.PRACTICE and not practice:
            raise serializers.ValidationError("practice_question is required when question_type=PRACTICE.")
        if mcq and practice:
            raise serializers.ValidationError("Provide only one of mcq_question or practice_question.")
        return attrs

    def create(self, validated_data):
        user = self.context["request"].user if "request" in self.context else None
        return QuestionReport.objects.create(reported_by=user, **validated_data)
