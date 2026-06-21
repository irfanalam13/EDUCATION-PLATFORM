export type MCQChoiceDTO = {
  id: number;
  choice_text: string;
};

export type MCQQuestionDTO = {
  id: number;
  topic: number;
  question_text: string;
  difficulty: "easy" | "medium" | "hard";
  choices: MCQChoiceDTO[];
};
