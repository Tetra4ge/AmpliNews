import { useState } from 'react';
import { ShieldAlert, Sparkles, CheckCircle, Mail } from 'lucide-react';
import { triggerUserDigest, type DigestTriggerResponse } from '../../lib/api';

interface EchoChamberBannerProps {
  leaning: number;
  totalRead: number;
}

export function EchoChamberBanner({ leaning, totalRead }: EchoChamberBannerProps) {
  const [loading, setLoading] = useState(false);
  const [digestResult, setDigestResult] = useState<DigestTriggerResponse | null>(null);
  const [showModal, setShowModal] = useState(false);

  const isEchoChamber = Math.abs(leaning) >= 0.35 && totalRead >= 3;
  const biasLabel = leaning < 0 ? 'Left' : 'Right';

  const handleGenerateDigest = async () => {
    try {
      setLoading(true);
      const res = await triggerUserDigest();
      setDigestResult(res.data);
      setShowModal(true);
    } catch (err) {
      console.error('Failed to trigger agent digest:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <div className={`mb-8 border p-5 shadow-sm transition-all ${
        isEchoChamber 
          ? 'border-amber-500/40 bg-amber-500/5' 
          : 'border-[var(--rule)] bg-[var(--card)]'
      }`}>
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-start gap-4">
            <div className={`mt-0.5 p-2 rounded-md ${
              isEchoChamber ? 'bg-amber-500/10 text-amber-600' : 'bg-[var(--accent)]/10 text-[var(--accent)]'
            }`}>
              {isEchoChamber ? <ShieldAlert size={20} /> : <Sparkles size={20} />}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="editorial-serif text-lg font-bold">
                  {isEchoChamber ? 'Echo Chamber Risk Alert' : 'Daily Agent Digest Machine'}
                </h3>
                <span className="editorial-mono text-[9px] uppercase tracking-widest px-2 py-0.5 bg-[var(--rule)] text-[var(--ink)]">
                  LangGraph Active
                </span>
              </div>
              <p className="editorial-mono mt-1 text-[10px] uppercase tracking-wider text-[var(--muted)]">
                {isEchoChamber
                  ? `Your reading diet skews ${biasLabel}-leaning. The agent has activated Perspective Check.`
                  : 'Synthesizing personalized news digest & perspective balance.'}
              </p>
            </div>
          </div>

          <button
            onClick={handleGenerateDigest}
            disabled={loading}
            className="flex items-center justify-center gap-2 border border-[var(--ink)] bg-[var(--ink)] text-[var(--paper)] px-4 py-2.5 editorial-mono text-[9px] uppercase tracking-widest transition-transform hover:-translate-y-0.5 disabled:opacity-50"
          >
            <Mail size={13} />
            {loading ? 'Synthesizing...' : 'Generate AI Email Digest'}
          </button>
        </div>
      </div>

      {showModal && digestResult && (
        <div className="fixed inset-0 z-[120] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm">
          <div className="relative w-full max-w-2xl max-h-[85vh] flex flex-col bg-[var(--paper)] border-2 border-[var(--ink)] shadow-[12px_12px_0_var(--accent)]">
            <div className="flex items-center justify-between border-b editorial-rule p-4 bg-[var(--paper-deep)]">
              <div className="flex items-center gap-2">
                <CheckCircle size={18} className="text-emerald-600" />
                <span className="editorial-serif font-bold text-lg">AI Digest Synthesized</span>
              </div>
              <button 
                onClick={() => setShowModal(false)}
                className="editorial-mono text-xs uppercase px-2 py-1 border border-[var(--rule)] hover:bg-[var(--rule)]"
              >
                Close
              </button>
            </div>

            <div className="p-6 overflow-y-auto space-y-4 editorial-mono text-xs">
              <div className="grid grid-cols-2 gap-3 p-3 bg-[var(--card)] border border-[var(--rule)]">
                <div>
                  <span className="text-[var(--muted)] block text-[9px]">ECHO CHAMBER RISK</span>
                  <span className="font-bold text-sm">{(digestResult.echo_chamber_risk * 100).toFixed(0)}%</span>
                </div>
                <div>
                  <span className="text-[var(--muted)] block text-[9px]">DOMINANT BIAS</span>
                  <span className="font-bold text-sm">{digestResult.dominant_bias}</span>
                </div>
                <div>
                  <span className="text-[var(--muted)] block text-[9px]">CURATED ARTICLES</span>
                  <span className="font-bold">{digestResult.articles_selected_count} stories</span>
                </div>
                <div>
                  <span className="text-[var(--muted)] block text-[9px]">PERSPECTIVE CHECKS</span>
                  <span className="font-bold text-amber-600">{digestResult.contrarian_articles_count} injected</span>
                </div>
              </div>

              <div>
                <p className="text-[9px] uppercase tracking-widest text-[var(--muted)] mb-2">HTML Email Preview</p>
                <div 
                  className="p-4 border border-[var(--rule)] bg-white text-black max-h-[300px] overflow-y-auto rounded text-xs"
                  dangerouslySetInnerHTML={{ __html: digestResult.html_preview }}
                />
              </div>
            </div>

            <div className="p-4 border-t editorial-rule bg-[var(--paper-deep)] flex justify-between items-center text-[10px] editorial-mono text-[var(--muted)]">
              <span>Status: {digestResult.status} | Email: {digestResult.email_status}</span>
              <button
                onClick={() => setShowModal(false)}
                className="px-4 py-2 bg-[var(--ink)] text-[var(--paper)] uppercase"
              >
                Done
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
