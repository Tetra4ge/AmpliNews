import { motion } from 'framer-motion';
import { X, Heart, AlertTriangle, RefreshCw } from 'lucide-react';
import type { OpposingViewResponse } from '../../lib/api';

interface ReadingModalProps {
  fullArticle: any;
  loadingArticle: boolean;
  isLiked: boolean;
  isBiased: boolean;
  opposingArticle: OpposingViewResponse | null;
  loadingOpposing: boolean;
  opposingError: string | null;
  onClose: () => void;
  onLike: () => void;
  onBiased: () => void;
  onOtherSide: () => void;
  onReadOpposing: (id: string) => void;
}

export function ReadingModal({
  fullArticle,
  loadingArticle,
  isLiked,
  isBiased,
  opposingArticle,
  loadingOpposing,
  opposingError,
  onClose,
  onLike,
  onBiased,
  onOtherSide,
  onReadOpposing
}: ReadingModalProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 sm:p-6 bg-[var(--ink)]/80 backdrop-blur-sm"
    >
      <motion.div
        initial={{ y: 50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        exit={{ y: 20, opacity: 0 }}
        className="relative flex h-full max-h-[90vh] w-full max-w-4xl flex-col bg-[var(--paper)] shadow-[12px_12px_0_var(--accent)]"
      >
        <div className="flex items-center justify-between border-b editorial-rule p-4 sm:p-6 bg-[var(--paper-deep)]">
          <div className="editorial-mono text-[10px] uppercase tracking-widest text-[var(--muted)]">
            {fullArticle ? fullArticle.metadata?.topic : 'Loading...'}
          </div>
          <button onClick={onClose} className="p-2 transition-colors hover:text-[var(--accent)]">
            <X size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-y-auto p-6 sm:p-10">
          {loadingArticle ? (
            <div className="flex h-full items-center justify-center">
              <p className="editorial-mono animate-pulse uppercase tracking-widest text-[var(--accent)]">
                Retrieving full text...
              </p>
            </div>
          ) : fullArticle ? (
            <div className="mx-auto max-w-2xl">
              <div className="mb-6 flex items-center gap-3 editorial-mono text-[9px] uppercase tracking-[.15em] text-[var(--accent)]">
                <span>{fullArticle.source}</span>
                <span>•</span>
                <span>{fullArticle.metadata?.bias}</span>
              </div>
              
              <h1 className="editorial-serif mb-8 text-3xl font-black leading-tight tracking-tight sm:text-5xl">
                {fullArticle.title}
              </h1>
              
              <div className="prose prose-stone prose-lg max-w-none editorial-serif text-[var(--ink)] leading-relaxed">
                {fullArticle.content.split('\n').map((paragraph: string, idx: number) => (
                  <p key={idx} className="mb-6">{paragraph}</p>
                ))}
              </div>

              {opposingError && (
                <div className="mt-8 border border-amber-500 bg-amber-50 p-4">
                  <p className="editorial-mono text-[10px] uppercase text-amber-700 font-bold">{opposingError}</p>
                </div>
              )}
              
              {opposingArticle && (
                <div className="mt-12 border-2 border-[var(--accent)] bg-[var(--card)] p-6 shadow-[8px_8px_0_var(--accent)] transition-all">
                  <div className="mb-4 flex items-center justify-between border-b editorial-rule pb-3">
                    <h3 className="editorial-serif text-2xl font-bold tracking-tight">Perspective Challenge</h3>
                    <span className="editorial-mono text-[9px] uppercase tracking-widest text-[var(--muted)]">Agent Suggestion</span>
                  </div>
                  <div className="mb-2 flex items-center gap-3 editorial-mono text-[9px] uppercase tracking-[.15em] text-[var(--accent)]">
                    <span className="font-bold">{opposingArticle.bias} Viewpoint</span>
                    <span>•</span>
                    <span>{Math.round(opposingArticle.similarity * 100)}% Match</span>
                  </div>
                  <h4 
                    className="editorial-serif text-xl font-medium leading-tight mb-4 cursor-pointer hover:text-[var(--accent)] transition-colors" 
                    onClick={() => onReadOpposing(opposingArticle.article_id)}
                  >
                    {opposingArticle.title}
                  </h4>
                  <button 
                    onClick={() => onReadOpposing(opposingArticle.article_id)}
                    className="editorial-mono text-[9px] uppercase tracking-widest underline decoration-[var(--accent)] underline-offset-4 text-[var(--ink)] hover:text-[var(--accent)]"
                  >
                    Read this perspective &rarr;
                  </button>
                </div>
              )}
            </div>
          ) : (
            <div className="flex h-full items-center justify-center">
              <p className="editorial-mono text-red-500">Failed to load article.</p>
            </div>
          )}
        </div>

        {fullArticle && !loadingArticle && (
          <div className="border-t editorial-rule bg-[var(--paper-deep)] p-4 sm:p-6">
            <div className="mx-auto flex max-w-2xl flex-wrap items-center justify-between gap-4">
              <a 
                href={fullArticle.url}
                target="_blank"
                rel="noopener noreferrer"
                className="editorial-mono text-[10px] uppercase tracking-widest underline decoration-[var(--rule)] underline-offset-4 transition-colors hover:text-[var(--accent)] hover:decoration-[var(--accent)]"
              >
                Read on Original Site
              </a>
              
              <div className="flex items-center gap-3">
                <button 
                  onClick={onLike}
                  className={`flex items-center gap-2 border px-4 py-2 transition-all hover:-translate-y-0.5 ${
                    isLiked 
                      ? 'border-red-500 bg-red-500/10 text-red-500 font-bold' 
                      : 'border-[var(--rule)] bg-[var(--card)] hover:border-[var(--accent)] hover:text-[var(--accent)]'
                  }`}
                >
                  <Heart size={14} className={isLiked ? 'fill-current' : ''} />
                  <span className="editorial-mono text-[9px] uppercase tracking-widest">{isLiked ? 'Liked' : 'Like'}</span>
                </button>
                
                <button 
                  onClick={onBiased}
                  className={`flex items-center gap-2 border px-4 py-2 transition-all hover:-translate-y-0.5 ${
                    isBiased 
                      ? 'border-amber-500 bg-amber-500/10 text-amber-500 font-bold' 
                      : 'border-[var(--rule)] bg-[var(--card)] hover:border-[var(--accent)] hover:text-[var(--accent)]'
                  }`}
                >
                  <AlertTriangle size={14} />
                  <span className="editorial-mono text-[9px] uppercase tracking-widest">{isBiased ? 'Biased Flagged' : 'Too Biased'}</span>
                </button>
                
                <button 
                  onClick={onOtherSide}
                  disabled={loadingOpposing}
                  className="flex items-center gap-2 bg-[var(--ink)] text-[var(--paper)] px-4 py-2 transition-all hover:-translate-y-0.5 shadow-[4px_4px_0_var(--accent)] disabled:opacity-50 disabled:hover:translate-y-0"
                >
                  <RefreshCw size={14} className={loadingOpposing ? "animate-spin" : ""} />
                  <span className="editorial-mono text-[9px] uppercase tracking-widest">{loadingOpposing ? 'Searching...' : 'Other Side'}</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </motion.div>
    </motion.div>
  );
}
