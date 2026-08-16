import { Bookmark } from 'lucide-react';
import type { Article } from '../../lib/api';

export function ArticleCard({ article, onClick }: { article: Article; onClick: (id: string) => void }) {
  return (
    <article 
      onClick={() => onClick(article.article_id)}
      className="group relative cursor-pointer flex flex-col justify-between border border-[var(--rule)] bg-[var(--card)] p-5 shadow-sm transition-all hover:-translate-y-1 hover:shadow-[6px_6px_0_var(--accent)]"
    >
      <div>
        <div className="mb-4 flex items-center justify-between border-b editorial-rule pb-3 editorial-mono text-[8px] uppercase tracking-[.15em] text-[var(--muted)]">
          <span>{article.source}</span>
          <Bookmark size={12} className="transition-colors group-hover:text-[var(--accent)]" />
        </div>
        <h3 className="editorial-serif mb-3 text-xl font-bold leading-tight tracking-tight group-hover:text-[var(--accent)] transition-colors">
          {article.title}
        </h3>
        <p className="text-sm leading-relaxed text-[var(--muted)] line-clamp-4">
          {article.reasoning}
        </p>
      </div>
      
      <div className="mt-6 border-t editorial-rule pt-4 flex items-center justify-between">
        <div className="editorial-mono text-[8px] uppercase tracking-widest">
          <span className="text-[var(--muted)]">Leaning: </span>
          <span className="font-bold text-[var(--ink)]">{article.bias}</span>
        </div>
        {article.match_percentage !== undefined && (
          <div className="editorial-mono text-[8px] uppercase tracking-widest text-[var(--accent)]">
            Match {article.match_percentage}%
          </div>
        )}
      </div>
    </article>
  );
}
