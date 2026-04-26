/**
 * src/components/advisor/AskPanel.jsx
 * -------------------------------------
 * RAG-powered pet-care Q&A panel — Pawsley persona (Phase 6).
 *
 * Renders the structured advisor response:
 *   answer    — main reply in Pawsley's friendly tone
 *   tips      — bite-sized actionable bullets
 *   vet_alert — amber warning callout when professional care may be needed
 *   sources   — knowledge-base chips
 *
 * Props: none
 */

import { useState } from 'react';
import { Sparkles, Lightbulb, BookOpen, TriangleAlert } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { askAdvisor } from '@/api/client';

export default function AskPanel() {
  const [question, setQuestion] = useState('');
  const [result, setResult]     = useState(null);   // AskOut | null
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');

  const handleAsk = async (e) => {
    e.preventDefault();
    const q = question.trim();
    if (!q) return;

    setLoading(true);
    setError('');
    setResult(null);

    try {
      setResult(await askAdvisor(q));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-4">

      {/* Question input */}
      <form onSubmit={handleAsk} className="flex flex-col gap-3">
        <div className="flex flex-col gap-1.5">
          <Label htmlFor="advisor-question">Ask Pawsley anything about pet care</Label>
          <div className="flex gap-2">
            <Input
              id="advisor-question"
              placeholder="How often should I bathe my dog?"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              disabled={loading}
              className="flex-1"
            />
            <Button type="submit" disabled={loading || !question.trim()}>
              <Sparkles className="h-4 w-4 mr-1.5" />
              {loading ? 'Asking…' : 'Ask'}
            </Button>
          </div>
        </div>
        {error && <p className="text-sm text-destructive">{error}</p>}
      </form>

      {/* Structured answer */}
      {result && (
        <>
          <Separator />
          <div className="flex flex-col gap-4">

            {/* Vet alert — shown first so it's impossible to miss */}
            {result.vet_alert && (
              <div className="flex gap-2 rounded-md border border-yellow-500/40 bg-yellow-500/10 p-3 text-sm text-yellow-800 dark:text-yellow-300">
                <TriangleAlert className="h-4 w-4 shrink-0 mt-0.5" />
                <p>{result.vet_alert}</p>
              </div>
            )}

            {/* Main answer */}
            <p className="text-sm leading-relaxed">{result.answer}</p>

            {/* Tips */}
            {result.tips?.length > 0 && (
              <div className="flex flex-col gap-1.5">
                <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground flex items-center gap-1">
                  <Lightbulb className="h-3 w-3" />
                  Quick tips
                </p>
                <ul className="flex flex-col gap-1 text-left">
                  {result.tips.map((tip, i) => (
                    <li key={i} className="flex gap-2 text-sm">
                      <span className="text-muted-foreground select-none">•</span>
                      <span>{tip}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Source chips */}
            {result.sources?.length > 0 && (
              <div className="flex flex-col gap-1.5">
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  <BookOpen className="h-3 w-3" />
                  Sources used
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {result.sources.map((s) => (
                    <span
                      key={s.id}
                      className="inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-medium text-muted-foreground"
                    >
                      {s.source === 'user-data' ? '📋 ' : '📚 '}
                      {s.title}
                    </span>
                  ))}
                </div>
              </div>
            )}

          </div>
        </>
      )}
    </div>
  );
}
