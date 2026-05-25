import { useState } from 'react';
import { Search as SearchIcon, Loader2, Sparkles, MessageSquare } from 'lucide-react';
import { Link } from 'react-router-dom';

interface SearchResult {
  answer: string;
  relevant_segments: {
    segment_id: number;
    meeting_id: number;
    meeting_title: string;
    text: string;
    distance: number;
  }[];
}

export default function SearchPage() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<SearchResult | null>(null);

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    try {
      const res = await fetch(`http://localhost:8000/api/search?query=${encodeURIComponent(query)}`);
      const data = await res.json();
      setResult(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in duration-500 pb-12">
      <header className="text-center mb-12">
        <h1 className="text-4xl font-bold tracking-tight mb-4 text-white flex items-center justify-center">
          <Sparkles className="w-8 h-8 text-primary mr-3" />
          Ask SmartConf AI
        </h1>
        <p className="text-gray-400 text-lg max-w-2xl mx-auto">
          Ask questions across all your previous meetings. The AI will synthesize an answer and show you the exact moments discussed.
        </p>
      </header>

      <form onSubmit={handleSearch} className="relative group z-20">
        <div className="absolute -inset-1 bg-gradient-to-r from-primary to-secondary rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-1000 group-hover:duration-200"></div>
        <div className="relative flex items-center bg-darker rounded-2xl p-2 border border-white/10">
          <SearchIcon className="w-6 h-6 text-gray-400 ml-4" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g. List the problems of MiniPC model sales..."
            className="flex-1 bg-transparent border-none text-white px-4 py-4 focus:outline-none focus:ring-0 text-lg placeholder-gray-500"
          />
          <button 
            type="submit"
            disabled={loading || !query.trim()}
            className="bg-primary hover:bg-indigo-600 text-white px-8 py-3 rounded-xl font-medium transition-colors disabled:opacity-50 flex items-center"
          >
            {loading ? <Loader2 className="w-5 h-5 animate-spin" /> : 'Ask AI'}
          </button>
        </div>
      </form>

      {result && (
        <div className="mt-12 space-y-8 animate-in slide-in-from-bottom-8 duration-700">
          {/* AI Answer */}
          <div className="glass-dark p-8 rounded-3xl border border-white/10 relative overflow-hidden">
            <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-primary to-secondary"></div>
            <h2 className="text-xl font-semibold mb-4 flex items-center text-white">
              <Sparkles className="w-5 h-5 mr-2 text-primary" />
              Synthesized Answer
            </h2>
            <div className="prose prose-invert max-w-none text-gray-300 leading-relaxed text-lg">
              {result.answer}
            </div>
          </div>

          {/* Sources */}
          <div>
            <h3 className="text-lg font-semibold mb-4 flex items-center text-gray-300">
              <MessageSquare className="w-5 h-5 mr-2 text-gray-400" />
              Relevant Excerpts
            </h3>
            <div className="grid gap-4 grid-cols-1 md:grid-cols-2">
              {result.relevant_segments.map((segment, idx) => (
                <div key={idx} className="glass p-5 rounded-2xl border border-white/5 hover:border-white/20 transition-colors">
                  <div className="flex justify-between items-start mb-3">
                    <Link to={`/meetings/${segment.meeting_id}`} className="font-medium text-primary hover:underline">
                      {segment.meeting_title}
                    </Link>
                    <span className="text-xs text-gray-500 bg-black/30 px-2 py-1 rounded">Score: {(1 - segment.distance).toFixed(2)}</span>
                  </div>
                  <p className="text-sm text-gray-400 italic line-clamp-4 leading-relaxed">"{segment.text}"</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
