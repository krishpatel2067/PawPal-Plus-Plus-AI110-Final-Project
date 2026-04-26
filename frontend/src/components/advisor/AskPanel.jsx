/**
 * src/components/advisor/AskPanel.jsx
 * -------------------------------------
 * RAG-powered pet-care Q&A panel.
 *
 * The user types a question, hits Ask, and gets a grounded answer from
 * Gemini alongside the knowledge-base chunks that were used to form it.
 *
 * Props: none (calls the API directly via askAdvisor)
 */

import { useState } from 'react';
import { Sparkles, BookOpen } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { askAdvisor } from '@/api/client';

export default function AskPanel() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer]     = useState('');
  const [sources, setSources]   = useState([]);
  const [loading, setLoading]   = useState(false);
  const [error, setError]       = useState('');

  const handleAsk = async (e) => {
    e.preventDefault();
    const q = question.trim();
    if (!q) return;

    setLoading(true);
    setError('');
    setAnswer('');
    setSources([]);

    try {
      const data = await askAdvisor(q);
      setAnswer(data.answer);
      setSources(data.sources);
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
          <Label htmlFor="advisor-question">Ask a pet-care question</Label>
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

      {/* Answer */}
      {answer && (
        <>
          <Separator />
          <div className="flex flex-col gap-3">
            <p className="text-sm leading-relaxed whitespace-pre-line">{answer}</p>

            {/* Source chips */}
            {sources.length > 0 && (
              <div className="flex flex-col gap-1.5">
                <p className="text-xs text-muted-foreground flex items-center gap-1">
                  <BookOpen className="h-3 w-3" />
                  Sources used
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {sources.map((s) => (
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
