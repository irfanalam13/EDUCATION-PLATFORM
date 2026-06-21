import Card from "@/shared/ui/Card";

export default function MCQScoreSummary({
  total,
  correct,
}: {
  total: number;
  correct: number;
}) {
  const wrong = total - correct;
  const percent = total === 0 ? 0 : Math.round((correct / total) * 100);

  return (
    <Card>
      <div className="flex flex-wrap gap-6 items-center justify-between">
        <div>
          <div className="text-lg font-semibold">Your Progress</div>
          <div className="text-sm opacity-70">Topic MCQ performance</div>
        </div>

        <div className="flex gap-6 text-sm">
          <div>
            <div className="font-medium text-green-700">{correct}</div>
            <div className="opacity-60">Correct</div>
          </div>
          <div>
            <div className="font-medium text-red-700">{wrong}</div>
            <div className="opacity-60">Wrong</div>
          </div>
          <div>
            <div className="font-medium">{percent}%</div>
            <div className="opacity-60">Score</div>
          </div>
        </div>
      </div>
    </Card>
  );
}
