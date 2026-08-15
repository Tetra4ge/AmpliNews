import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="border-t editorial-rule bg-[var(--paper)] py-10">
      <div className="landing-shell flex flex-col items-center justify-between gap-6 sm:flex-row">
        <div className="flex flex-col items-center gap-3 sm:items-start">
          <Link to="/" className="editorial-serif text-2xl font-black tracking-[-.08em]">
            ampli<span style={{ color: 'var(--accent)' }}>.</span>news
          </Link>
          <p className="editorial-mono text-[9px] uppercase tracking-[.1em]" style={{ color: 'var(--muted)' }}>
            © {new Date().getFullYear()} AmpliNews. All rights reserved.
          </p>
        </div>
        
        <div className="flex items-center gap-6 editorial-mono text-[10px] font-medium uppercase tracking-wider text-[var(--ink)]">
          <a href="#" className="transition-colors hover:text-[var(--accent)]">X (Twitter)</a>
          <a href="#" className="transition-colors hover:text-[var(--accent)]">LinkedIn</a>
          <a href="#" className="transition-colors hover:text-[var(--accent)]">GitHub</a>
        </div>
      </div>
    </footer>
  );
}
