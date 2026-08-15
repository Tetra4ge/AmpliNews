import { ArrowDownRight, Check } from 'lucide-react';

const steps = [
  ['Tell us your beat', 'Choose the subjects you keep coming back to. Politics, climate, business, culture—your desk starts with you.'],
  ['Read your brief', 'Open a calm, considered daily edition assembled from across the news landscape.'],
  ['Grow your view', 'Follow the thread, compare the coverage, and find the perspective that makes the story fuller.'],
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="scroll-mt-8 border-y editorial-rule bg-[var(--paper-deep)] py-16 sm:py-24">
      <div className="landing-shell grid gap-12 lg:grid-cols-[.8fr_1.2fr]">
        <div><p className="editorial-label">The reading ritual</p><h2 className="editorial-serif mt-4 max-w-md text-5xl font-black leading-[.88] tracking-[-.07em] sm:text-6xl">A wider world,<br /><em style={{ color: 'var(--accent)' }}>one edition</em><br />at a time.</h2><div className="mt-9 flex items-center gap-3 editorial-mono text-[10px] uppercase tracking-[.1em]" style={{ color: 'var(--muted)' }}><span className="grid h-7 w-7 place-items-center rounded-full border editorial-rule"><ArrowDownRight size={14} /></span> Three minutes to begin</div></div>
        <div className="divide-y editorial-rule border-t editorial-rule">
          {steps.map(([title, text], index) => <div key={title} className="grid gap-3 py-7 sm:grid-cols-[64px_1fr_auto] sm:items-start"><span className="editorial-serif text-3xl font-bold" style={{ color: 'var(--accent)' }}>0{index + 1}</span><div><h3 className="editorial-serif text-2xl font-bold tracking-[-.04em]">{title}</h3><p className="mt-2 max-w-md text-sm leading-6" style={{ color: 'var(--muted)' }}>{text}</p></div><span className="mt-1 grid h-6 w-6 place-items-center rounded-full border editorial-rule"><Check size={12} /></span></div>)}
        </div>
      </div>
    </section>
  );
}
