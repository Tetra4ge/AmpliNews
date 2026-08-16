import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import Lenis from 'lenis';
import { ArrowUpRight, Menu, Moon, Sun, X } from 'lucide-react';
import Hero from '../components/landing/Hero';
import Features from '../components/landing/Features';
import HowItWorks from '../components/landing/HowItWorks';
import CallToAction from '../components/landing/CallToAction';
import Footer from '../components/landing/Footer';
import { useTheme } from '../hooks/useTheme';

export default function LandingPage() {
  const { theme, toggleTheme } = useTheme();
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    const lenis = new Lenis({ duration: 1.1, smoothWheel: true, touchMultiplier: 1.4 });
    let frame = 0;
    const raf = (time: number) => { lenis.raf(time); frame = requestAnimationFrame(raf); };
    frame = requestAnimationFrame(raf);
    return () => { cancelAnimationFrame(frame); lenis.destroy(); };
  }, []);

  const scrollTo = (id: string) => {
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    setMenuOpen(false);
  };

  return (
    <main className="landing-page paper-grain" data-theme={theme}>
      <div className="border-b editorial-rule overflow-hidden py-2.5 whitespace-nowrap">
        <div className="ticker-track editorial-mono text-[10px] tracking-[.15em] uppercase" style={{ color: 'var(--muted)' }}>
          {["A broader view of the world", "Personal news, without the echo", "Issue No. 01 — The daily edition", "Read beyond your point of view"].map((item) => (
            <span className="mr-12" key={item}>✦&nbsp;&nbsp;{item}</span>
          ))}
          {["A broader view of the world", "Personal news, without the echo", "Issue No. 01 — The daily edition", "Read beyond your point of view"].map((item) => (
            <span className="mr-12" key={`${item}-repeat`}>✦&nbsp;&nbsp;{item}</span>
          ))}
        </div>
      </div>

      <header className="landing-shell flex min-h-[86px] items-center justify-between border-b editorial-rule">
        <Link to="/" className="editorial-serif text-[1.72rem] font-black tracking-[-.08em] sm:text-[2.05rem]">ampli<span style={{ color: 'var(--accent)' }}>.</span>news</Link>
        <nav className="hidden items-center gap-7 md:flex editorial-mono text-[11px] font-medium uppercase tracking-[.1em]" style={{ color: 'var(--muted)' }}>
          <button onClick={() => scrollTo('the-edition')} className="cursor-pointer border-0 bg-transparent transition-colors hover:text-[var(--ink)]">The edition</button>
          <button onClick={() => scrollTo('how-it-works')} className="cursor-pointer border-0 bg-transparent transition-colors hover:text-[var(--ink)]">Our method</button>
        </nav>
        <div className="flex items-center gap-3">
          <button
            onClick={(event) => {
              const bounds = event.currentTarget.getBoundingClientRect();
              toggleTheme({ x: event.clientX || bounds.left + bounds.width / 2, y: event.clientY || bounds.top + bounds.height / 2 });
            }}
            className="theme-toggle-button grid h-9 w-9 cursor-pointer place-items-center rounded-full border editorial-rule bg-transparent transition-transform hover:scale-105"
            aria-label="Toggle color theme"
          >
            {theme === 'light' ? <Moon size={15} strokeWidth={1.7} /> : <Sun size={16} strokeWidth={1.7} />}
          </button>
          <Link to="/login" className="hidden items-center gap-2 px-4 py-2.5 editorial-mono text-[10px] font-medium uppercase tracking-[.1em] transition-transform hover:-translate-y-0.5 sm:flex" style={{ backgroundColor: 'var(--ink)', color: 'var(--paper)' }}>Start reading <ArrowUpRight size={13} /></Link>
          <button onClick={() => setMenuOpen(!menuOpen)} className="grid h-9 w-9 cursor-pointer place-items-center border editorial-rule bg-transparent md:hidden" aria-label="Open menu">{menuOpen ? <X size={18} /> : <Menu size={19} />}</button>
        </div>
      </header>

      {menuOpen && <nav className="landing-shell border-b editorial-rule py-5 md:hidden"><div className="grid gap-4 editorial-mono text-xs uppercase tracking-[.1em]"><button onClick={() => scrollTo('the-edition')} className="w-fit cursor-pointer border-0 bg-transparent">The edition</button><button onClick={() => scrollTo('how-it-works')} className="w-fit cursor-pointer border-0 bg-transparent">Our method</button></div></nav>}

      <Hero />
      <Features />
      <HowItWorks />
      <CallToAction />

      <Footer />
    </main>
  );
}
