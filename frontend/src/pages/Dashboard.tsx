import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { fetchUserProfile, syncUser, type UserProfileResponse } from '../lib/api';

const TOPICS = ['Politics', 'Tech', 'Health', 'Sports', 'Business'];

type ViewState = 'loading' | 'onboarding' | 'ready' | 'error';

export default function Dashboard() {
  const navigate = useNavigate();
  const [view, setView] = useState<ViewState>('loading');
  const [profile, setProfile] = useState<UserProfileResponse | null>(null);
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [leaning, setLeaning] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        navigate('/login', { replace: true });
        return;
      }

      try {
        const res = await fetchUserProfile();
        if (!cancelled) {
          setProfile(res.data);
          setView('ready');
        }
      } catch (err: any) {
        if (cancelled) return;
        // No profile yet -> first-time login, show interest onboarding (docs/flow.md Step 1).
        if (err?.response?.status === 404) {
          setView('onboarding');
        } else {
          setError('Could not reach AmpliNews API.');
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
      <main className="min-h-screen bg-[#0a0a0a] text-neutral-400 flex items-center justify-center">
        <p className="text-sm">Loading...</p>
      </main>
    );
  }

  if (view === 'error') {
    return (
      <main className="min-h-screen bg-[#0a0a0a] text-neutral-200 flex items-center justify-center">
        <p className="text-sm text-red-400">{error}</p>
      </main>
    );
  }

  if (view === 'onboarding') {
    return (
      <main className="min-h-screen bg-[#0a0a0a] text-neutral-200 flex items-center justify-center px-4">
        <form
          onSubmit={handleOnboardingSubmit}
          className="w-full max-w-md border border-[#222] bg-black/40 p-8 space-y-6"
        >
          <div>
            <h1 className="font-logo text-xl mb-1">Let's personalize your news</h1>
            <p className="text-sm text-neutral-500">What interests you?</p>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {TOPICS.map((topic) => (
              <label
                key={topic}
                className={`border px-3 py-2 text-sm cursor-pointer select-none ${
                  selectedTopics.includes(topic)
                    ? 'border-neutral-200 bg-neutral-100 text-black'
                    : 'border-[#333] text-neutral-300'
                }`}
              >
                <input
                  type="checkbox"
                  className="hidden"
                  checked={selectedTopics.includes(topic)}
                  onChange={() => toggleTopic(topic)}
                />
                {topic}
              </label>
            ))}
          </div>

          <div>
            <label htmlFor="leaning" className="block text-xs text-neutral-500 mb-2">
              Political leaning (optional): {leaning.toFixed(1)}
              <span className="ml-2 text-neutral-600">
                {leaning <= -0.34 ? 'Left-leaning' : leaning >= 0.34 ? 'Right-leaning' : 'Center'}
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
              className="w-full"
            />
          </div>

          {error && <p className="text-xs text-red-400">{error}</p>}

          <button
            type="submit"
            disabled={selectedTopics.length === 0 || submitting}
            className="w-full bg-neutral-100 text-black py-2 text-sm font-semibold disabled:opacity-50"
          >
            {submitting ? 'Saving...' : 'Start reading'}
          </button>
        </form>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-neutral-200 px-4 py-10">
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="font-logo text-xl">AmpliNews</h1>
          <button onClick={handleSignOut} className="text-xs text-neutral-500 hover:text-neutral-200">
            Sign out
          </button>
        </div>

        <div className="grid grid-cols-3 gap-4">
          <Stat label="Articles Read" value={profile?.total_articles_read ?? 0} />
          <Stat label="Top Topic" value={profile?.most_read_topic ?? '—'} />
          <Stat
            label="Baseline Leaning"
            value={formatLeaning(profile?.baseline_political_leaning ?? 0)}
          />
        </div>

        <p className="mt-8 text-sm text-neutral-500">
          Your personalized feed is being built. Check back soon.
        </p>
      </div>
    </main>
  );
}

function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="border border-[#222] p-4">
      <p className="text-xs text-neutral-500 mb-1">{label}</p>
      <p className="text-lg">{value}</p>
    </div>
  );
}

function formatLeaning(value: number) {
  if (value <= -0.34) return `Left (${value.toFixed(1)})`;
  if (value >= 0.34) return `Right (${value.toFixed(1)})`;
  return `Center (${value.toFixed(1)})`;
}
