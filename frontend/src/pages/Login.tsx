import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';

export default function Login() {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [status, setStatus] = useState<'idle' | 'sending' | 'sent' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);

  // If already logged in (or a magic-link redirect just completed), skip straight to the dashboard.
  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      if (data.session) navigate('/dashboard', { replace: true });
    });

    const { data: subscription } = supabase.auth.onAuthStateChange((_event, session) => {
      if (session) navigate('/dashboard', { replace: true });
    });

    return () => subscription.subscription.unsubscribe();
  }, [navigate]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setStatus('sending');
    setError(null);

    const { error: signInError } = await supabase.auth.signInWithOtp({
      email,
      options: { emailRedirectTo: `${window.location.origin}/dashboard` },
    });

    if (signInError) {
      setStatus('error');
      setError(signInError.message);
      return;
    }
    setStatus('sent');
  }

  return (
    <main className="min-h-screen bg-[#0a0a0a] text-neutral-200 flex items-center justify-center px-4">
      <div className="w-full max-w-sm border border-[#222] bg-black/40 p-8">
        <h1 className="font-logo text-2xl mb-1">AmpliNews</h1>
        <p className="text-sm text-neutral-500 mb-6">Sign in to personalize your feed.</p>

        {status === 'sent' ? (
          <p className="text-sm text-green-400">
            Check <span className="text-neutral-200">{email}</span> for a magic sign-in link.
          </p>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label htmlFor="email" className="block text-xs text-neutral-500 mb-1">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="w-full bg-black border border-[#333] px-3 py-2 text-sm outline-none focus:border-neutral-500"
              />
            </div>

            {error && <p className="text-xs text-red-400">{error}</p>}

            <button
              type="submit"
              disabled={status === 'sending'}
              className="w-full bg-neutral-100 text-black py-2 text-sm font-semibold disabled:opacity-50"
            >
              {status === 'sending' ? 'Sending link...' : 'Continue with email'}
            </button>
          </form>
        )}
      </div>
    </main>
  );
}
