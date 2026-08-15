import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { fetchUserProfile, syncUser, fetchFeed, type UserProfileResponse, type Article } from '../lib/api';
import { ArrowUpRight, LogOut, Compass, Bookmark } from 'lucide-react';

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
            <Stat label="AI Vector Bias" value={formatLeaning(profile?.baseline_political_leaning ?? 0)} />
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
              <article key={article.article_id} className="group relative flex flex-col justify-between border border-[var(--rule)] bg-[var(--card)] p-5 shadow-sm transition-all hover:-translate-y-1 hover:shadow-[6px_6px_0_var(--accent)]">
                <div>
                  <div className="mb-4 flex items-center justify-between border-b editorial-rule pb-3 editorial-mono text-[8px] uppercase tracking-[.15em] text-[var(--muted)]">
                    <span>{article.source}</span>
                    <Bookmark size={12} className="transition-colors group-hover:text-[var(--accent)]" />
                  </div>
                  <a href={article.url} target="_blank" rel="noopener noreferrer">
                    <h3 className="editorial-serif mb-3 text-xl font-bold leading-tight tracking-tight hover:text-[var(--accent)] transition-colors">
                      {article.title}
                    </h3>
                  </a>
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
