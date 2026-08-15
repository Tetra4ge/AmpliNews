import { ArrowUpRight, Scale, ScanSearch, Sparkles } from 'lucide-react';

const features = [
  { number: '01', icon: ScanSearch, label: 'The signal desk', title: 'Less noise. More that matters.', text: 'Our agents scan across trusted sources and surface the stories genuinely worth your attention—not just the loudest ones.' },
  { number: '02', icon: Scale, label: 'The context desk', title: 'Every angle, in one place.', text: 'We trace the framing, source credibility, and competing views around every story so you can read with your eyes open.' },
  { number: '03', icon: Sparkles, label: 'The you desk', title: 'A paper that gets smarter.', text: 'Your edition evolves with every read, helping you follow your interests while gently widening the frame.' },
];

export default function Features() {
  return (
    <section id="the-edition" className="landing-shell scroll-mt-8 py-16 sm:py-24">
      <div className="grid gap-7 border-y editorial-rule py-7 md:grid-cols-[.8fr_1.2fr] md:items-end">
        <div><p className="editorial-label">The AmpliNews difference</p><p className="editorial-serif mt-2 text-3xl font-bold tracking-[-.05em]">A new kind of morning paper.</p></div>
        <p className="max-w-xl text-sm leading-6 md:justify-self-end" style={{ color: 'var(--muted)' }}>Editorial judgment meets adaptive intelligence. The result is an edition that respects your time and expands your thinking.</p>
      </div>
      <div className="grid divide-y editorial-rule md:grid-cols-3 md:divide-x md:divide-y-0">
        {features.map(({ number, icon: Icon, label, title, text }) => <article key={number} className="group py-9 md:px-7 md:first:pl-0 md:last:pr-0"><div className="flex items-start justify-between"><span className="editorial-mono text-[10px] tracking-wider" style={{ color: 'var(--muted)' }}>{number}</span><Icon size={22} strokeWidth={1.3} style={{ color: 'var(--accent)' }} /></div><p className="editorial-label mt-12">{label}</p><h3 className="editorial-serif mt-3 text-[1.8rem] font-bold leading-[.95] tracking-[-.05em]">{title}</h3><p className="mt-4 text-sm leading-6" style={{ color: 'var(--muted)' }}>{text}</p><span className="mt-7 inline-flex items-center gap-1 editorial-mono text-[10px] uppercase tracking-wider transition-transform group-hover:translate-x-1">Read the philosophy <ArrowUpRight size={13} /></span></article>)}
      </div>
    </section>
  );
}
