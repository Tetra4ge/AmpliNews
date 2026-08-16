import { Link, useNavigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { ArrowUpRight, LogOut, Compass } from 'lucide-react';
import { useDashboard } from '../hooks/useDashboard';
import { ArticleCard } from '../components/dashboard/ArticleCard';
import { ReadingModal } from '../components/dashboard/ReadingModal';
import { Stat } from '../components/dashboard/Stat';
import { formatLeaning } from '../utils/formatters';

const TOPICS = ['Politics', 'Tech', 'Health', 'Sports', 'Business'];

export default function Dashboard() {
  const navigate = useNavigate();
  const {
    view,
    profile,
    feed,
    selectedTopics,
    leaning,
    submitting,
    error,
    debugLog,
    selectedArticleId,
    fullArticle,
    loadingArticle,
    isLiked,
    isBiased,
    opposingArticle,
    loadingOpposing,
    opposingError,
    setLeaning,
    toggleTopic,
    handleOnboardingSubmit,
    handleSignOut,
    handleArticleClick,
    closeReadingView,
    handleLikeClick,
    handleBiasedClick,
    handleOtherSideClick
  } = useDashboard(navigate);

  if (view === 'loading') {
    return (
      <main className="landing-page paper-grain flex min-h-screen items-center justify-center flex-col gap-4">
        <p className="editorial-mono text-xs uppercase tracking-widest text-[var(--muted)]">Loading your edition...</p>
        <p className="editorial-mono text-[10px] text-[var(--accent)]">{debugLog}</p>
      </main>
    );
  }

  if (view === 'error') {
    return (
      <main className="landing-page paper-grain flex min-h-screen items-center justify-center">
        <p className="editorial-mono text-xs font-bold uppercase tracking-widest text-[var(--accent)]">{error}</p>
      </main>
    );
  }

  if (view === 'onboarding') {
    return (
      <main className="landing-page paper-grain flex min-h-screen items-center justify-center px-4 py-12">
        <form
          onSubmit={handleOnboardingSubmit}
          className="w-full max-w-[540px] border border-[var(--ink)] bg-[var(--card)] p-6 shadow-[8px_8px_0_var(--accent)] backdrop-blur-md sm:p-10"
        >
          <div className="mb-8 text-center">
            <h1 className="editorial-serif text-3xl font-black tracking-[-.05em] sm:text-4xl">Curate your perspective.</h1>
            <p className="editorial-mono mt-3 text-[10px] uppercase tracking-[.1em]" style={{ color: 'var(--muted)' }}>
              Select topics you care about to build your initial AI profile.
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
                  onChange={() => toggleTopic(topic)}
                />
                <span className="editorial-mono text-[10px] font-medium uppercase tracking-widest">{topic}</span>
              </label>
            ))}
          </div>

          <div className="mb-8 border-t border-[var(--rule)] pt-6">
            <label htmlFor="leaning" className="mb-4 flex items-center justify-between editorial-mono text-[9px] uppercase tracking-[.1em] text-[var(--ink)]">
              <span>Political baseline (optional)</span>
              <span className="font-bold">
                {leaning <= -0.34 ? 'Left' : leaning >= 0.34 ? 'Right' : 'Center'} ({leaning.toFixed(1)})
              </span>
            </label>
            <input
              id="leaning"
              type="range"
              min={-1}
              max={1}
              step={0.1}
              value={leaning}
              onChange={(e) => setLeaning(Number(e.target.value))}
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
            {submitting ? 'Generating AI Profile...' : 'Build my edition'}
            {submitting ? null : <ArrowUpRight size={15} />}
          </button>
        </form>
      </main>
    );
  }

  return (
    <main className="landing-page paper-grain min-h-screen pb-24">
      <header className="border-b editorial-rule sticky top-0 z-50 bg-[var(--paper)]/90 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <Link to="/" className="editorial-serif text-2xl font-black tracking-[-.08em]">
            ampli<span style={{ color: 'var(--accent)' }}>.</span>news
          </Link>
          <button 
            onClick={handleSignOut} 
            className="flex items-center gap-2 editorial-mono text-[9px] font-medium uppercase tracking-[.1em] text-[var(--muted)] transition-colors hover:text-[var(--accent)]"
          >
            Sign out <LogOut size={13} />
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-6 pt-12">
        <div className="mb-12 flex flex-col items-start justify-between gap-6 md:flex-row md:items-end">
          <div>
            <p className="editorial-label mb-3">Your Reader Profile</p>
            <h1 className="editorial-serif text-4xl font-bold tracking-[-.04em] sm:text-5xl">The Daily Digest.</h1>
          </div>
          <div className="flex w-full overflow-x-auto divide-x editorial-rule border border-[var(--rule)] bg-[var(--card)] p-4 shadow-sm backdrop-blur-sm md:w-auto">
            <Stat label="Articles Read" value={profile?.total_articles_read ?? 0} />
            <Stat label="Top Topic" value={profile?.most_read_topic ?? '—'} />
            <div className="px-5 first:pl-2 last:pr-2 min-w-[200px]">
              <p className="editorial-mono mb-2 text-[8px] uppercase tracking-widest text-[var(--muted)] flex justify-between">
                <span>Left</span>
                <span className="font-bold text-[var(--ink)]">{formatLeaning(profile?.baseline_political_leaning ?? 0)}</span>
                <span>Right</span>
              </p>
              <div className="h-1.5 w-full bg-[var(--rule)] rounded-full overflow-hidden relative">
                <div 
                  className="absolute top-0 h-full bg-[var(--accent)] transition-all duration-1000"
                  style={{ 
                    left: '50%', 
                    width: `${Math.abs((profile?.baseline_political_leaning ?? 0) * 50)}%`,
                    transform: (profile?.baseline_political_leaning ?? 0) < 0 ? 'translateX(-100%)' : 'none'
                  }}
                />
                <div className="absolute top-0 left-1/2 w-px h-full bg-[var(--ink)]/30 -translate-x-1/2" />
              </div>
            </div>
          </div>
        </div>

        <div className="mb-8 flex items-center justify-between border-b editorial-rule pb-4">
          <h2 className="editorial-serif text-2xl font-bold tracking-tight">Curated for you</h2>
          <span className="editorial-mono text-[10px] uppercase tracking-widest text-[var(--muted)]">
            Powered by pgvector
          </span>
        </div>

        {feed.length === 0 ? (
          <div className="flex min-h-[300px] flex-col items-center justify-center border border-dashed border-[var(--rule)] p-8 text-center">
             <div className="mb-4 grid h-12 w-12 place-items-center rounded-full bg-[var(--accent)]/10 text-[var(--accent)]">
               <Compass size={24} />
             </div>
             <p className="editorial-serif text-xl font-medium">Scanning the globe...</p>
             <p className="editorial-mono mt-3 max-w-sm text-[10px] uppercase tracking-widest text-[var(--muted)]">
               Our AI is analyzing thousands of articles to match your vector embedding.
             </p>
          </div>
        ) : (
          <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
            {feed.map((article) => (
              <ArticleCard 
                key={article.article_id}
                article={article}
                onClick={handleArticleClick}
              />
            ))}
          </div>
        )}
      </div>

      <AnimatePresence>
        {selectedArticleId && (
          <ReadingModal 
            fullArticle={fullArticle}
            loadingArticle={loadingArticle}
            isLiked={isLiked}
            isBiased={isBiased}
            opposingArticle={opposingArticle}
            loadingOpposing={loadingOpposing}
            opposingError={opposingError}
            onClose={closeReadingView}
            onLike={handleLikeClick}
            onBiased={handleBiasedClick}
            onOtherSide={handleOtherSideClick}
            onReadOpposing={handleArticleClick}
          />
        )}
      </AnimatePresence>
    </main>
  );
}
