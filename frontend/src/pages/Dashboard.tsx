import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { AnimatePresence, motion } from 'framer-motion';
import { fetchUserProfile, syncUser, fetchFeed, fetchArticleById, logArticleRead, type UserProfileResponse, type Article } from '../lib/api';
import { ArrowUpRight, LogOut, Compass, Bookmark, X, Heart, AlertTriangle, RefreshCw } from 'lucide-react';

const TOPICS = ['Politics', 'Tech', 'Health', 'Sports', 'Business'];

type ViewState = 'loading' | 'onboarding' | 'ready' | 'error';

export default function Dashboard() {
  const navigate = useNavigate();
  const [view, setView] = useState<ViewState>('loading');
  const [profile, setProfile] = useState<UserProfileResponse | null>(null);
  const [feed, setFeed] = useState<Article[]>([]);
  
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [leaning, setLeaning] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [debugLog, setDebugLog] = useState<string>('Starting load...');

  // Reading View State
  const [selectedArticleId, setSelectedArticleId] = useState<string | null>(null);
  const [fullArticle, setFullArticle] = useState<any | null>(null);
  const [loadingArticle, setLoadingArticle] = useState(false);
  const [readStartTime, setReadStartTime] = useState<number | null>(null);
  const [isLiked, setIsLiked] = useState<boolean>(false);
  const [isBiased, setIsBiased] = useState<boolean>(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setDebugLog('Checking session...');
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        navigate('/login', { replace: true });
        return;
      }

      try {
        setDebugLog('Fetching user profile...');
        const res = await fetchUserProfile();
        if (!cancelled) {
          setDebugLog('Profile fetched. Setting ready...');
          setProfile(res.data);
          setView('ready');
          
          // Fetch feed immediately after profile is ready
          try {
            const feedRes = await fetchFeed();
            if (!cancelled) {
              setFeed(feedRes.data.feed || []);
            }
          } catch (feedErr) {
            console.error("Could not fetch feed", feedErr);
          }
        }
      } catch (err: any) {
        if (cancelled) return;
        setDebugLog(`Error occurred: ${err.message}`);
        if (err?.response?.status === 404) {
          setView('onboarding');
        } else {
          const detail = err?.response?.data?.detail || err.message;
          setError(`API Error: ${detail}`);
          setView('error');
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [navigate]);

  function toggleTopic(topic: string) {
    setSelectedTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
    );
  }

  async function handleOnboardingSubmit(e: FormEvent) {
    e.preventDefault();
    if (selectedTopics.length === 0) return;
    setSubmitting(true);
    setError(null);

    try {
      await syncUser({ selected_topics: selectedTopics, baseline_leaning: leaning });
      const res = await fetchUserProfile();
      setProfile(res.data);
      setView('ready');
      
      const feedRes = await fetchFeed();
      setFeed(feedRes.data.feed || []);
    } catch {
      setError('Failed to save your preferences. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  async function handleSignOut() {
    await supabase.auth.signOut();
    navigate('/login', { replace: true });
  }

  async function handleArticleClick(id: string) {
    setSelectedArticleId(id);
    setReadStartTime(Date.now());
    setIsLiked(false);
    setIsBiased(false);
    setLoadingArticle(true);
    setFullArticle(null);
    try {
      const res = await fetchArticleById(id);
      setFullArticle(res.data);
    } catch (err) {
      console.error("Failed to fetch full article", err);
    } finally {
      setLoadingArticle(false);
    }
  }

  async function closeReadingView() {
    if (selectedArticleId && readStartTime) {
      const duration = Math.max(0, Math.round((Date.now() - readStartTime) / 1000));
      try {
        await logArticleRead({
          article_id: selectedArticleId,
          read_duration_seconds: duration,
          liked: isLiked,
          rejected_biased: isBiased
        });
      } catch (err) {
        console.error("Failed to log reading interaction", err);
      }
    }
    setSelectedArticleId(null);
    setFullArticle(null);
    setReadStartTime(null);
    setIsLiked(false);
    setIsBiased(false);
  }

  async function handleLikeClick() {
    if (!selectedArticleId) return;
    const newLiked = !isLiked;
    setIsLiked(newLiked);
    if (newLiked) setIsBiased(false);

    const duration = readStartTime ? Math.max(0, Math.round((Date.now() - readStartTime) / 1000)) : 0;
    try {
      await logArticleRead({
        article_id: selectedArticleId,
        read_duration_seconds: duration,
        liked: newLiked,
        rejected_biased: false
      });
    } catch (err) {
      console.error("Failed to log like interaction", err);
    }
  }

  async function handleBiasedClick() {
    if (!selectedArticleId) return;
    const newBiased = !isBiased;
    setIsBiased(newBiased);
    if (newBiased) setIsLiked(false);

    const duration = readStartTime ? Math.max(0, Math.round((Date.now() - readStartTime) / 1000)) : 0;
    try {
      await logArticleRead({
        article_id: selectedArticleId,
        read_duration_seconds: duration,
        liked: false,
        rejected_biased: newBiased
      });
    } catch (err) {
      console.error("Failed to log biased interaction", err);
    }
  }

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
              <article 
                key={article.article_id} 
                onClick={() => handleArticleClick(article.article_id)}
                className="group relative cursor-pointer flex flex-col justify-between border border-[var(--rule)] bg-[var(--card)] p-5 shadow-sm transition-all hover:-translate-y-1 hover:shadow-[6px_6px_0_var(--accent)]"
              >
                <div>
                  <div className="mb-4 flex items-center justify-between border-b editorial-rule pb-3 editorial-mono text-[8px] uppercase tracking-[.15em] text-[var(--muted)]">
                    <span>{article.source}</span>
                    <Bookmark size={12} className="transition-colors group-hover:text-[var(--accent)]" />
                  </div>
                  <h3 className="editorial-serif mb-3 text-xl font-bold leading-tight tracking-tight group-hover:text-[var(--accent)] transition-colors">
                    {article.title}
                  </h3>
                  <p className="text-sm leading-relaxed text-[var(--muted)] line-clamp-4">
                    {article.reasoning}
                  </p>
                </div>
                
                <div className="mt-6 border-t editorial-rule pt-4 flex items-center justify-between">
                  <div className="editorial-mono text-[8px] uppercase tracking-widest">
                    <span className="text-[var(--muted)]">Leaning: </span>
                    <span className="font-bold text-[var(--ink)]">{article.bias}</span>
                  </div>
                  {article.match_percentage !== undefined && (
                    <div className="editorial-mono text-[8px] uppercase tracking-widest text-[var(--accent)]">
                      Match {article.match_percentage}%
                    </div>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </div>

      <AnimatePresence>
        {selectedArticleId && (
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
                <button onClick={closeReadingView} className="p-2 transition-colors hover:text-[var(--accent)]">
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
                        onClick={handleLikeClick}
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
                        onClick={handleBiasedClick}
                        className={`flex items-center gap-2 border px-4 py-2 transition-all hover:-translate-y-0.5 ${
                          isBiased 
                            ? 'border-amber-500 bg-amber-500/10 text-amber-500 font-bold' 
                            : 'border-[var(--rule)] bg-[var(--card)] hover:border-[var(--accent)] hover:text-[var(--accent)]'
                        }`}
                      >
                        <AlertTriangle size={14} />
                        <span className="editorial-mono text-[9px] uppercase tracking-widest">{isBiased ? 'Biased Flagged' : 'Too Biased'}</span>
                      </button>
                      
                      <button className="flex items-center gap-2 bg-[var(--ink)] text-[var(--paper)] px-4 py-2 transition-all hover:-translate-y-0.5 shadow-[4px_4px_0_var(--accent)]">
                        <RefreshCw size={14} />
                        <span className="editorial-mono text-[9px] uppercase tracking-widest">Other Side</span>
                      </button>
                    </div>
                  </div>
                </div>
              )}
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="px-5 first:pl-2 last:pr-2 whitespace-nowrap">
      <p className="editorial-mono text-[8px] uppercase tracking-widest text-[var(--muted)]">{label}</p>
      <p className="editorial-serif mt-1 text-xl font-semibold">{value}</p>
    </div>
  );
}

function formatLeaning(value: number) {
  if (value <= -0.34) return `Left (${value.toFixed(1)})`;
  if (value >= 0.34) return `Right (${value.toFixed(1)})`;
  return `Center (${value.toFixed(1)})`;
}
