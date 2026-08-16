export function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="px-5 first:pl-2 last:pr-2 whitespace-nowrap">
      <p className="editorial-mono text-[8px] uppercase tracking-widest text-[var(--muted)]">{label}</p>
      <p className="editorial-serif mt-1 text-xl font-semibold">{value}</p>
    </div>
  );
}
