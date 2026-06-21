"use client";

import { useEffect, useState } from "react";
import { contentClient } from "../../api/content.client";
import type { Flashcard, FlashcardDeck, ReviewSessionItem } from "../../types/content.types";

export default function FlashcardsPanel({ topicId }: { topicId: number }) {
  const [decks, setDecks] = useState<FlashcardDeck[]>([]);
  const [deckId, setDeckId] = useState<number | null>(null);

  const [cards, setCards] = useState<Flashcard[]>([]);
  const [front, setFront] = useState("");
  const [back, setBack] = useState("");

  const [queue, setQueue] = useState<ReviewSessionItem[]>([]);
  const [qIndex, setQIndex] = useState(0);
  const [showBack, setShowBack] = useState(false);

  async function loadDecks() {
    const d = await contentClient.listDecks({ topic: topicId });
    setDecks(d);
    if (!deckId && d.length) setDeckId(d[0].id);
  }

  async function loadCards(selectedDeckId: number) {
    const c = await contentClient.listFlashcards({ deck: selectedDeckId });
    setCards(c);
  }

  async function loadQueue(selectedDeckId: number) {
    const q = await contentClient.getReviewQueue({ deck: selectedDeckId, limit: 20 });
    setQueue(q);
    setQIndex(0);
    setShowBack(false);
  }

  useEffect(() => {
    loadDecks();
  }, [topicId]);

  useEffect(() => {
    if (!deckId) return;
    loadCards(deckId);
    loadQueue(deckId);
  }, [deckId]);

  async function createCard() {
    if (!deckId || !front.trim() || !back.trim()) return;
    await contentClient.createFlashcard({ deck: deckId, front, back });
    setFront("");
    setBack("");
    await loadCards(deckId);
    await loadQueue(deckId);
  }

  async function grade(gradeValue: 0 | 1 | 2 | 3) {
    const item = queue[qIndex];
    if (!item) return;

    await contentClient.gradeReview({ card_id: item.card_id, grade: gradeValue });

    // move next
    const nextIndex = Math.min(qIndex + 1, queue.length);
    setQIndex(nextIndex);
    setShowBack(false);
  }

  const current = queue[qIndex];

  return (
    <div className="space-y-4">
      <div className="rounded-xl border p-4 space-y-3">
        <div className="font-semibold">Flashcards</div>

        <div className="flex gap-2 items-center flex-wrap">
          <select
            className="rounded-lg border p-2 text-sm"
            value={deckId ?? ""}
            onChange={(e) => setDeckId(Number(e.target.value))}
          >
            {decks.map((d) => (
              <option key={d.id} value={d.id}>
                {d.title}
              </option>
            ))}
          </select>
        </div>

        <div className="grid gap-2">
          <input
            className="rounded-lg border p-2 text-sm"
            placeholder="Front"
            value={front}
            onChange={(e) => setFront(e.target.value)}
          />
          <textarea
            className="rounded-lg border p-2 text-sm"
            placeholder="Back"
            value={back}
            onChange={(e) => setBack(e.target.value)}
          />
          <button onClick={createCard} className="rounded-lg bg-black text-white px-4 py-2 text-sm">
            Add Card
          </button>
        </div>
      </div>

      <div className="rounded-xl border p-4 space-y-3">
        <div className="font-semibold">SRS Review</div>

        {!current ? (
          <div className="text-sm text-gray-600">No due cards right now.</div>
        ) : (
          <div className="space-y-3">
            <div className="rounded-lg border p-4 text-center">
              <div className="text-xs text-gray-500 mb-2">
                Card {qIndex + 1} / {queue.length}
              </div>

              <div className="text-lg font-semibold">
                {showBack ? current.back : current.front}
              </div>

              <button onClick={() => setShowBack((s) => !s)} className="underline text-sm mt-2">
                Flip
              </button>
            </div>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              <button onClick={() => grade(0)} className="rounded-lg border px-3 py-2 text-sm hover:bg-gray-50">
                Again
              </button>
              <button onClick={() => grade(1)} className="rounded-lg border px-3 py-2 text-sm hover:bg-gray-50">
                Hard
              </button>
              <button onClick={() => grade(2)} className="rounded-lg border px-3 py-2 text-sm hover:bg-gray-50">
                Good
              </button>
              <button onClick={() => grade(3)} className="rounded-lg border px-3 py-2 text-sm hover:bg-gray-50">
                Easy
              </button>
            </div>
          </div>
        )}
      </div>

      <div className="rounded-xl border p-4 space-y-2">
        <div className="font-semibold">All Cards</div>
        <div className="grid gap-2">
          {cards.map((c) => (
            <div key={c.id} className="rounded-lg border p-3 text-sm">
              <div className="font-medium">{c.front}</div>
              <div className="text-gray-600 mt-1">{c.back}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
