import { useEffect, useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { supabase } from '../lib/supabase';
import { ArrowUpRight } from 'lucide-react';

export default function Login() {
  const navigate = useNavigate();
  const [mode, setMode] = useState<'login' | 'signup'>('login');
  
  // Form State
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [name, setName] = useState('');
  
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [error, setError] = useState<string | null>(null);

  // If already logged in, skip straight to the dashboard.
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
    setStatus('loading');
    setError(null);

    if (mode === 'signup') {
      if (password.length < 6) {
        setError('Password must be at least 6 characters long');
        setStatus('error');
        return;
      }
      if (password !== confirmPassword) {
        setError('Passwords do not match');
        setStatus('error');
        return;
      }
      if (name.trim().length < 2) {
        setError('Please enter a valid full name');
        setStatus('error');
        return;
      }
      
      const { error: signUpError } = await supabase.auth.signUp({
        email,
        password,
        options: {
          data: {
            full_name: name,
          }
        }
      });

      if (signUpError) {
        setStatus('error');
        setError(signUpError.message);
        return;
      }
      
      setStatus('success');
      
    } else {
      const { error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password
      });

      if (signInError) {
        setStatus('error');
        setError(signInError.message);
        return;
      }
    }
  }

  return (
    <main className="landing-page paper-grain flex min-h-screen items-center justify-center px-4 py-12">
      <div className="w-full max-w-[380px] border border-[var(--ink)] bg-[var(--card)] p-6 shadow-[6px_6px_0_var(--accent)] backdrop-blur-md sm:p-8">
        <div className="mb-8 flex flex-col items-center text-center">
          <h1 className="editorial-serif text-3xl font-black tracking-[-.08em]">
            ampli<span style={{ color: 'var(--accent)' }}>.</span>news
          </h1>
          <p className="editorial-mono mt-3 text-[9px] uppercase tracking-[.1em]" style={{ color: 'var(--muted)' }}>
            {mode === 'login' ? 'Sign in to access your edition' : 'Join to build your edition'}
          </p>
        </div>

        <div className="mb-6 flex border-b border-[var(--rule)]">
          <button 
            type="button" 
            onClick={() => { setMode('login'); setError(null); }}
            className={`flex-1 pb-3 editorial-mono text-[10px] font-semibold uppercase tracking-[.1em] transition-colors ${mode === 'login' ? 'border-b-2 border-[var(--accent)] text-[var(--ink)]' : 'text-[var(--muted)] hover:text-[var(--ink)]'}`}
          >
            Sign In
          </button>
          <button 
            type="button" 
            onClick={() => { setMode('signup'); setError(null); }}
            className={`flex-1 pb-3 editorial-mono text-[10px] font-semibold uppercase tracking-[.1em] transition-colors ${mode === 'signup' ? 'border-b-2 border-[var(--accent)] text-[var(--ink)]' : 'text-[var(--muted)] hover:text-[var(--ink)]'}`}
          >
            Create Account
          </button>
        </div>

        {status === 'success' && mode === 'signup' ? (
          <div className="text-center py-4">
            <p className="editorial-serif text-lg leading-relaxed">
              Your account has been created.
            </p>
            <p className="editorial-mono mt-4 text-[10px] leading-relaxed tracking-[.05em]" style={{ color: 'var(--muted)' }}>
              Please check <span className="font-bold text-[var(--ink)]">{email}</span> for a confirmation link.
            </p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {mode === 'signup' && (
              <div>
                <label htmlFor="name" className="editorial-label mb-1.5 block text-[8px]">
                  Full Name
                </label>
                <input
                  id="name"
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Jane Doe"
                  className="w-full border-b border-[var(--rule)] bg-transparent py-2 text-sm outline-none transition-colors placeholder:text-[var(--muted)] focus:border-[var(--ink)] editorial-mono"
                />
              </div>
            )}
            
            <div>
              <label htmlFor="email" className="editorial-label mb-1.5 block text-[8px]">
                Email Address
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="reader@example.com"
                className="w-full border-b border-[var(--rule)] bg-transparent py-2 text-sm outline-none transition-colors placeholder:text-[var(--muted)] focus:border-[var(--ink)] editorial-mono"
              />
            </div>

            <div>
              <label htmlFor="password" className="editorial-label mb-1.5 block text-[8px]">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full border-b border-[var(--rule)] bg-transparent py-2 text-sm outline-none transition-colors placeholder:text-[var(--muted)] focus:border-[var(--ink)] editorial-mono"
              />
            </div>
            
            {mode === 'signup' && (
              <div>
                <label htmlFor="confirmPassword" className="editorial-label mb-1.5 block text-[8px]">
                  Re-enter Password
                </label>
                <input
                  id="confirmPassword"
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full border-b border-[var(--rule)] bg-transparent py-2 text-sm outline-none transition-colors placeholder:text-[var(--muted)] focus:border-[var(--ink)] editorial-mono"
                />
              </div>
            )}

            {error && <p className="editorial-mono text-[9px] font-semibold text-[var(--accent)]">{error}</p>}

            <button
              type="submit"
              disabled={status === 'loading'}
              className="mt-2 flex w-full items-center justify-center gap-3 px-5 py-3.5 editorial-mono text-[10px] font-medium uppercase tracking-[.1em] transition-transform hover:-translate-y-1 disabled:opacity-50 disabled:hover:translate-y-0"
              style={{ backgroundColor: 'var(--ink)', color: 'var(--paper)' }}
            >
              {status === 'loading' ? 'Processing...' : (mode === 'login' ? 'Sign In' : 'Create Account')}
              {status !== 'loading' && <ArrowUpRight size={14} />}
            </button>
          </form>
        )}
      </div>
    </main>
  );
}
