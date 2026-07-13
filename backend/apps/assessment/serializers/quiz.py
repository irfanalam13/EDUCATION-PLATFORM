from rest_framework import serializers

from apps.assessment.models import QuizSession
from apps.assessment.models.quiz import QuizMode


class QuizStartSerializer(serializers.Serializer):
    scope = serializers.DictField(required=False, default=dict)  # {"subject":"..","chapter":"..","topic":".."}
    count = serializers.IntegerField(min_value=1, max_value=200)
    mode = serializers.ChoiceField(choices=QuizMode.choices, default=QuizMode.PRACTICE)
    difficulty_mix = serializers.DictField(required=False, default=dict)

    def validate_difficulty_mix(self, mix):
        # Allow empty => will be treated as all MEDIUM or evenly in selector
        allowed = {"EASY", "MEDIUM", "HARD"}
        for k, v in mix.items():
            if k not in allowed:
                raise serializers.ValidationError(f"Invalid difficulty key: {k}")
            try:
                fv = float(v)
            except Exception:
                raise serializers.ValidationError("difficulty_mix values must be numbers.")
            if fv < 0:
                raise serializers.ValidationError("difficulty_mix values must be >= 0.")
        return mix


class QuizSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizSession
        fields = [
            "id",
            "mode",
            "state",
            "subject",
            "chapter",
            "topic",
            "requested_count",
            "difficulty_mix",
            "started_at",
            "finished_at",
            "created_at",
        ]


class QuizQuestionSerializer(serializers.Serializer):
    """
    Returns question without correct answer.
    """
    id = serializers.IntegerField()
    title = serializers.CharField(allow_blank=True)
    question_text = serializers.CharField()
    difficulty = serializers.CharField()
    subject = serializers.CharField(allow_blank=True)
    chapter = serializers.CharField(allow_blank=True)
    topic = serializers.CharField(allow_blank=True)
    options = serializers.ListField(child=serializers.DictField())


class QuizAnswerSerializer(serializers.Serializer):
    question_id = serializers.IntegerField()
    answer = serializers.IntegerField()  # option_id
    time_spent_seconds = serializers.IntegerField(min_value=0, max_value=60 * 60)

    def validate(self, attrs):
        # Basic checks (deep checks done in service)
        return attrs


class QuizFinishSerializer(serializers.Serializer):
    # no input required, but keep serializer for consistency
    pass


class QuizReviewSerializer(serializers.Serializer):
    """
    Returns correct answers + explanation after finish.
    """
    session = QuizSessionSerializer()
    result = serializers.DictField()
    questions = serializers.ListField(child=serializers.DictField())
