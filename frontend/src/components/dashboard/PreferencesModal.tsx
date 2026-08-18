import { motion } from 'framer-motion';
import type { FormEvent } from 'react';
import { X, ArrowUpRight } from 'lucide-react';
import { TOPICS } from '../../utils/constants';

interface PreferencesModalProps {
  selectedTopics: string[];
  leaning: number;
  submitting: boolean;
  error: string | null;
  onToggleTopic: (topic: string) => void;
  onLeaningChange: (value: number) => void;
  onSubmit: (e: FormEvent) => void;
  onClose: () => void;
}

export function PreferencesModal({
  selectedTopics,
  leaning,
  submitting,
  error,
  onToggleTopic,
  onLeaningChange,
  onSubmit,
  onClose
}: PreferencesModalProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 bg-[var(--ink)]/80 backdrop-blur-sm"
    >
      <motion.form
        onSubmit={onSubmit}
        initial={{ y: 30, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 20, opacity: 0 }}
        className="relative w-full max-w-[540px] border border-[var(--ink)] bg-[var(--card)] p-6 shadow-[8px_8px_0_var(--accent)] sm:p-10"
      >
        <button
          type="button"
          onClick={onClose}
          className="absolute right-4 top-4 p-2 transition-colors hover:text-[var(--accent)]"
          aria-label="Close preferences"
        >
          <X size={18} />
        </button>

        <div className="mb-8 text-center">
          <h1 className="editorial-serif text-3xl font-black tracking-[-.05em]">Edit your preferences.</h1>
          <p className="editorial-mono mt-3 text-[10px] uppercase tracking-[.1em]" style={{ color: 'var(--muted)' }}>
            Re-select the topics you care about to retrain your AI profile.
          </p>
        </div>

        <div className="mb-8 grid grid-cols-2 gap-3 sm:grid-cols-3">
          {TOPICS.map((topic) => (
            <label
              key={topic}
              className={`flex cursor-pointer select-none items-center justify-center border border-[var(--rule)] px-3 py-3 text-center transition-colors ${
                selectedTopics.includes(topic)
                  ? 'border-[var(--ink)] bg-[var(--ink)] text-[var(--paper)]'
                  : 'bg-transparent text-[var(--ink)] hover:bg-[var(--rule)]'
              }`}
            >
              <input
                type="checkbox"
                className="hidden"
                checked={selectedTopics.includes(topic)}
                onChange={() => onToggleTopic(topic)}
              />
              <span className="editorial-mono text-[10px] font-medium uppercase tracking-widest">{topic}</span>
            </label>
          ))}
        </div>

        <div className="mb-8 border-t border-[var(--rule)] pt-6">
          <label htmlFor="pref-leaning" className="mb-4 flex items-center justify-between editorial-mono text-[9px] uppercase tracking-[.1em] text-[var(--ink)]">
            <span>Political baseline (optional)</span>
            <span className="font-bold">
              {leaning <= -0.34 ? 'Left' : leaning >= 0.34 ? 'Right' : 'Center'} ({leaning.toFixed(1)})
            </span>
          </label>
          <input
            id="pref-leaning"
            type="range"
            min={-1}
            max={1}
            step={0.1}
            value={leaning}
            onChange={(e) => onLeaningChange(Number(e.target.value))}
            className="w-full cursor-pointer accent-[var(--ink)]"
          />
          <div className="mt-2 flex justify-between editorial-mono text-[8px] uppercase tracking-wider text-[var(--muted)]">
            <span>Left</span>
            <span>Center</span>
            <span>Right</span>
          </div>
        </div>

        {error && <p className="mb-4 editorial-mono text-[9px] font-semibold text-[var(--accent)]">{error}</p>}

        <button
          type="submit"
          disabled={selectedTopics.length === 0 || submitting}
          className="flex w-full items-center justify-center gap-3 px-6 py-4 editorial-mono text-[11px] font-medium uppercase tracking-[.1em] transition-transform hover:-translate-y-1 disabled:opacity-50 disabled:hover:translate-y-0"
          style={{ backgroundColor: 'var(--ink)', color: 'var(--paper)' }}
        >
          {submitting ? 'Updating AI Profile...' : 'Save preferences'}
          {submitting ? null : <ArrowUpRight size={15} />}
        </button>
      </motion.form>
    </motion.div>
  );
}
