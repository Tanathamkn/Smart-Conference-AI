import { useState } from 'react';
import { Search as SearchIcon, Loader2, Sparkles, MessageSquare, SlidersHorizontal, X } from 'lucide-react';
import { Link } from 'react-router-dom';

interface SearchSegment {
  segment_id: number;
  meeting_id: number;
  meeting_title: string;
  meeting_date: string;
  text: string;
  hybrid_score: number;
  rerank_score?: number;
}

interface SearchResult {
  answer: string;
  expanded_query: string;
  relevant_segments: SearchSegment[];
}

interface Filters {
  date_from: string;
  date_to: string;
  meeting_id: string;
  mmr: boolean;
  rerank: boolean;
}

const DEFAULT_FILTERS: Filters = {
  date_from: '',
  date_to: '',
  meeting_id: '',
  mmr: true,
  rerank: true,
};

// Score → colour: green ≥ 0.7, yellow ≥ 0.4, red < 0.4
function scoreColour(score: number): string {
  if (score >= 0.7) return 'text-emerald-400 bg-emerald-400/10';
  if (score >= 0.4) return 'text-yellow-400 bg-yellow-400/10';
  return 'text-red-400 bg-red-400/10';
}

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<Filters>(DEFAULT_FILTERS);
  const [showFilters, setShowFilters] = useState(false);

  // ── Search ────────────────────────────────────────────────────────────────

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const params = new URLSearchParams({ query: query.trim() });
      if (filters.date_from) params.append('date_from', filters.date_from);
      if (filters.date_to) params.append('date_to', filters.date_to);
      if (filters.meeting_id) params.append('meeting_id', filters.meeting_id);
      params.append('mmr', String(filters.mmr));
      params.append('rerank', String(filters.rerank));

      const res = await fetch(`http://localhost:8000/api/search?${params}`);
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      setResult(await res.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Search failed.');
    } finally {
      setLoading(false);
    }
  };

  const clearFilters = () => setFilters(DEFAULT_FILTERS);
  const activeFilterCount = [
    filters.date_from,
    filters.date_to,
    filters.meeting_id,
  ].filter(Boolean).length + (filters.mmr ? 0 : 1) + (filters.rerank ? 0 : 1);

  // ── Render ────────────────────────────────────────────────────────────────

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500 pb-12">

      {/* Header */}
      <header className="text-center mb-12">
        <h1 className="text-4xl font-bold tracking-tight mb-4 text-white flex items-center justify-center">
          <Sparkles className="w-8 h-8 text-primary mr-3" />
          Ask SmartConf AI
        </h1>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
          Ask questions across all your previous meetings. The AI will synthesise
          an answer and show you the exact moments discussed.
        </p>
      </header>

      {/* Search bar */}
      <form onSubmit={handleSearch} className="space-y-3">
        <div className="relative group z-20">
          <div className="absolute -inset-1 bg-gradient-to-r from-primary to-secondary rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200" />
          <div className="relative flex items-center bg-darker rounded-2xl p-2 border border-white/10">
            <SearchIcon className="w-6 h-6 text-gray-400 ml-4 flex-shrink-0" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. What were the sales issues discussed last quarter?"
              className="flex-1 bg-transparent border-none text-white px-4 py-4 focus:outline-none focus:ring-0 text-lg placeholder-gray-500"
            />

            {/* Filter toggle */}
            <button
              type="button"
              onClick={() => setShowFilters((v) => !v)}
              className={`relative mr-2 p-2.5 rounded-xl transition-colors ${showFilters ? 'bg-primary/20 text-primary' : 'text-gray-400 hover:text-white hover:bg-white/10'
                }`}
              title="Filters"
            >
              <SlidersHorizontal className="w-5 h-5" />
              {activeFilterCount > 0 && (
                <span className="absolute -top-1 -right-1 w-4 h-4 bg-primary text-white text-[10px] font-bold rounded-full flex items-center justify-center">
                  {activeFilterCount}
                </span>
              )}
            </button>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="bg-primary hover:bg-indigo-600 text-white px-8 py-3 rounded-xl font-medium transition-colors disabled:opacity-50 flex items-center gap-2"
            >
              {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Ask AI'}
            </button>
          </div>
        </div>

        {/* Filter panel */}
        {showFilters && (
          <div className="bg-darker border border-white/10 rounded-2xl p-5 space-y-4 animate-in slide-in-from-top-2 duration-200">
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-semibold text-white">Search filters</span>
              {activeFilterCount > 0 && (
                <button
                  type="button"
                  onClick={clearFilters}
                  className="text-xs text-gray-400 hover:text-white flex items-center gap-1"
                >
                  <X className="w-3 h-3" /> Clear all
                </button>
              )}
            </div>

            {/* Date range */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Date from</label>
                <input
                  type="date"
                  value={filters.date_from}
                  onChange={(e) => setFilters((f) => ({ ...f, date_from: e.target.value }))}
                  className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Date to</label>
                <input
                  type="date"
                  value={filters.date_to}
                  onChange={(e) => setFilters((f) => ({ ...f, date_to: e.target.value }))}
                  className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-primary"
                />
              </div>
            </div>

            {/* Meeting ID */}
            <div>
              <label className="text-xs text-gray-400 mb-1 block">Restrict to meeting ID</label>
              <input
                type="number"
                value={filters.meeting_id}
                onChange={(e) => setFilters((f) => ({ ...f, meeting_id: e.target.value }))}
                placeholder="Leave blank to search all meetings"
                className="w-full bg-black/30 border border-white/10 rounded-lg px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-primary"
              />
            </div>

            {/* Toggles */}
            <div className="flex gap-6">
              {(
                [
                  { key: 'mmr' as const, label: 'MMR diversity', hint: 'Prevents one meeting from dominating results' },
                  { key: 'rerank' as const, label: 'Cross-encoder rerank', hint: 'Higher precision, slightly slower' },
                ] as const
              ).map(({ key, label, hint }) => (
                <label key={key} className="flex items-start gap-2 cursor-pointer group/toggle">
                  <div className="relative mt-0.5">
                    <input
                      type="checkbox"
                      checked={filters[key]}
                      onChange={(e) => setFilters((f) => ({ ...f, [key]: e.target.checked }))}
                      className="sr-only"
                    />
                    <div className={`w-8 h-4 rounded-full transition-colors ${filters[key] ? 'bg-primary' : 'bg-white/20'}`}>
                      <div className={`w-3 h-3 bg-white rounded-full absolute top-0.5 transition-transform ${filters[key] ? 'translate-x-4' : 'translate-x-0.5'}`} />
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-white">{label}</div>
                    <div className="text-xs text-gray-500">{hint}</div>
                  </div>
                </label>
              ))}
            </div>
          </div>
        )}
      </form>

      {/* Error */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="mt-12 space-y-8 animate-in slide-in-from-bottom-8 duration-700">

          {/* Expanded query pill — transparency for the user */}
          {result.expanded_query && result.expanded_query !== query && (
            <div className="flex items-center gap-2 text-sm text-gray-400">
              <Sparkles className="w-4 h-4 text-primary flex-shrink-0" />
              <span>Searched as:</span>
              <span className="text-gray-200 italic">"{result.expanded_query}"</span>
            </div>
          )}

          {/* AI answer */}
          <div className="glass-dark p-8 rounded-3xl border border-white/10 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-primary to-secondary" />
            <h2 className="text-xl font-semibold mb-4 flex items-center text-white">
              <Sparkles className="w-5 h-5 mr-2 text-primary" />
              Synthesised Answer
            </h2>
            <div className="prose prose-invert max-w-none text-gray-300 leading-relaxed text-lg">
              {result.answer}
            </div>
          </div>

          {/* Source segments */}
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center text-gray-300">
              <MessageSquare className="w-5 h-5 mr-2 text-gray-400" />
              Relevant Excerpts
              <span className="ml-2 text-sm font-normal text-gray-500">
                ({result.relevant_segments.length} found)
              </span>
            </h3>

            <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
              {result.relevant_segments.map((segment, idx) => {
                // Use rerank_score when available, fall back to hybrid_score
                const displayScore = segment.rerank_score !== undefined
                  ? segment.rerank_score
                  : segment.hybrid_score;
                const colourClass = scoreColour(displayScore);

                return (
                  <div
                    key={idx}
                    className="glass p-5 rounded-2xl border border-white/5 hover:border-white/20 transition-colors"
                  >
                    <div className="flex justify-between items-start mb-2">
                      <Link
                        to={`/meetings/${segment.meeting_id}`}
                        className="font-medium text-primary hover:underline text-sm leading-snug"
                      >
                        {segment.meeting_title}
                      </Link>
                      <span className={`text-xs font-semibold px-2 py-1 rounded-full ml-2 flex-shrink-0 ${colourClass}`}>
                        {displayScore.toFixed(2)}
                      </span>
                    </div>

                    {segment.meeting_date && (
                      <div className="text-xs text-gray-600 mb-2">{segment.meeting_date}</div>
                    )}

                    <p className="text-sm text-gray-400 italic line-clamp-4 leading-relaxed">
                      "{segment.text}"
                    </p>

                    {/* Score breakdown tooltip row */}
                    {segment.rerank_score !== undefined && (
                      <div className="mt-3 pt-3 border-t border-white/5 flex gap-3 text-xs text-gray-600">
                        <span>hybrid {segment.hybrid_score.toFixed(3)}</span>
                        <span>·</span>
                        <span>rerank {segment.rerank_score.toFixed(3)}</span>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
