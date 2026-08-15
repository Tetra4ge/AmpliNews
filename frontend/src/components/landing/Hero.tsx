import { ArrowDown, ArrowUpRight, Bookmark, Compass, Sparkles } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Hero() {
  return (
    <section className="landing-shell pt-10 sm:pt-16">
      <div className="flex items-center justify-between border-y editorial-rule py-3 editorial-mono text-[10px] uppercase tracking-[.12em]" style={{ color: 'var(--muted)' }}>
        <span>Saturday, August 15, 2026</span><span className="hidden sm:inline">Independent ideas · intentionally assembled</span><span>New Delhi · 27°C</span>
      </div>
      <div className="grid gap-10 py-12 lg:grid-cols-[1.08fr_.92fr] lg:items-center lg:py-20">
        <div>
          <p className="editorial-label reveal mb-5">Your personal daily edition</p>
          <h1 className="editorial-serif reveal delay-1 max-w-4xl text-[clamp(3.55rem,8.2vw,7.9rem)] font-black leading-[.84] tracking-[-.075em]">News with<br /><em className="font-semibold" style={{ color: 'var(--accent)' }}>more</em> than one<br />side of the story.</h1>
          <p className="reveal delay-2 mt-7 max-w-lg text-base leading-7 sm:text-lg" style={{ color: 'var(--muted)' }}>A daily intelligence brief that learns what matters to you—and makes room for the perspectives that challenge you.</p>
          <div className="reveal delay-3 mt-9 flex flex-wrap items-center gap-4">
            <Link to="/login" className="inline-flex items-center gap-3 bg-[var(--accent)] px-5 py-3.5 editorial-mono text-[11px] font-medium uppercase tracking-[.1em] text-white transition-transform hover:-translate-y-1">Build my edition <ArrowUpRight size={15} /></Link>
            <a href="#the-edition" className="inline-flex items-center gap-2 px-2 py-3 editorial-mono text-[11px] font-medium uppercase tracking-[.1em] underline decoration-[var(--accent)] underline-offset-4">Explore the paper <ArrowDown size={14} /></a>
          </div>
          <div className="mt-11 flex items-center gap-3 editorial-mono text-[10px] uppercase tracking-[.11em]" style={{ color: 'var(--muted)' }}><span className="h-px w-8 bg-[var(--accent)]" /> No doom scroll. Just context.</div>
        </div>

        <div className="relative mx-auto w-full max-w-[530px]">
          <div className="floating-note absolute -left-3 top-12 z-10 hidden max-w-[145px] border border-[var(--rule)] bg-[var(--paper)] p-3 shadow-lg sm:block"><div className="editorial-label text-[8px]">Different angle</div><p className="mt-2 editorial-serif text-sm leading-4">One story. Three lenses. Your view gets wider.</p></div>
          <article className="relative overflow-hidden border border-[var(--ink)] bg-[var(--card)] p-4 shadow-[10px_10px_0_var(--accent)] backdrop-blur-sm sm:p-6">
            <div className="flex items-center justify-between border-b editorial-rule pb-3 editorial-mono text-[9px] uppercase tracking-[.13em]" style={{ color: 'var(--muted)' }}><span>AmplinNews / Brief 021</span><Bookmark size={13} /></div>
            <p className="editorial-label mt-6">Technology · featured analysis</p>
            <h2 className="editorial-serif mt-3 text-3xl font-bold leading-[.95] tracking-[-.05em] sm:text-4xl">The quiet shift changing how we work.</h2>
            <div className="mt-6 grid grid-cols-3 divide-x editorial-rule border-y py-3">
              <div className="pr-3"><p className="editorial-mono text-[8px] uppercase tracking-wider" style={{ color: 'var(--muted)' }}>Signal</p><p className="mt-1 text-xs font-semibold">High</p></div>
              <div className="px-3"><p className="editorial-mono text-[8px] uppercase tracking-wider" style={{ color: 'var(--muted)' }}>Sources</p><p className="mt-1 text-xs font-semibold">07</p></div>
              <div className="pl-3"><p className="editorial-mono text-[8px] uppercase tracking-wider" style={{ color: 'var(--muted)' }}>Read time</p><p className="mt-1 text-xs font-semibold">4 min</p></div>
            </div>
            <div className="mt-5 flex items-center gap-3"><div className="grid h-9 w-9 place-items-center rounded-full bg-[var(--accent)] text-white"><Compass size={17} /></div><p className="text-xs leading-4" style={{ color: 'var(--muted)' }}>See the prevailing take <br />and the perspective missing from it.</p></div>
          </article>
          <div className="absolute -bottom-7 right-1 z-10 flex items-center gap-2 border border-[var(--rule)] bg-[var(--paper)] px-3 py-2 shadow-md sm:right-8"><Sparkles size={13} style={{ color: 'var(--accent)' }} /><span className="editorial-mono text-[9px] uppercase tracking-wider">Curated for your curiosity</span></div>
        </div>
      </div>
    </section>
  );
}
