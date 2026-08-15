import { ArrowUpRight, CheckCircle2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function CallToAction() {
  return (
    <section className="landing-shell py-16 sm:py-24">
      <div className="relative overflow-hidden border border-[var(--ink)] px-6 py-12 text-center sm:px-12 sm:py-20">
        <div className="absolute -left-24 -top-28 h-64 w-64 rounded-full bg-[var(--accent)] opacity-15 blur-3xl" /><div className="absolute -bottom-32 -right-16 h-64 w-64 rounded-full bg-[var(--accent)] opacity-10 blur-3xl" />
        <div className="relative mx-auto max-w-3xl"><p className="editorial-label">Your first edition awaits</p><h2 className="editorial-serif mt-5 text-[clamp(3.1rem,7vw,6.2rem)] font-black leading-[.84] tracking-[-.075em]">Make room for<br />a <em style={{ color: 'var(--accent)' }}>better</em> point of view.</h2><p className="mx-auto mt-7 max-w-lg text-base leading-7" style={{ color: 'var(--muted)' }}>Build a calmer, smarter relationship with the news. Your daily brief is ready when you are.</p><Link to="/login" className="mt-9 inline-flex items-center gap-3 bg-[var(--ink)] px-6 py-4 editorial-mono text-[11px] font-medium uppercase tracking-[.1em] text-[var(--paper)] transition-transform hover:-translate-y-1">Create my edition <ArrowUpRight size={15} /></Link><div className="mt-7 flex flex-wrap justify-center gap-x-5 gap-y-2 editorial-mono text-[9px] uppercase tracking-[.1em]" style={{ color: 'var(--muted)' }}><span className="inline-flex items-center gap-1"><CheckCircle2 size={12} /> Free to start</span><span className="inline-flex items-center gap-1"><CheckCircle2 size={12} /> No noisy feed</span><span className="inline-flex items-center gap-1"><CheckCircle2 size={12} /> Built around you</span></div></div>
      </div>
    </section>
  );
}
