import { useEffect, useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Calendar, CheckCircle, AlertTriangle, FileText, Loader2, ArrowLeft, Trash2 } from 'lucide-react';

interface ActionItem {
  id: number;
  owner: string;
  task: string;
  status: string;
}

interface Issue {
  id: number;
  product: string;
  problem: string;
  solution: string;
}

interface MeetingDetails {
  id: number;
  title: string;
  date: string;
  transcript: string;
  summary: string;
  action_items: ActionItem[];
  issues: Issue[];
}

export default function MeetingDetailsPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [meeting, setMeeting] = useState<MeetingDetails | null>(null);
  const [loading, setLoading] = useState(true);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    let timeoutId: number;

    const fetchMeeting = () => {
      fetch(`http://localhost:8000/api/meetings/${id}`)
        .then(res => res.json())
        .then(data => {
          setMeeting(data);
          setLoading(false);

          // Poll again if still processing
          if (!data.summary && !data.transcript) {
            timeoutId = window.setTimeout(fetchMeeting, 3000);
          }
        })
        .catch(err => {
          console.error("Failed to fetch meeting", err);
          setLoading(false);
        });
    };

    fetchMeeting();

    return () => {
      if (timeoutId) window.clearTimeout(timeoutId);
    };
  }, [id]);

  const handleDelete = async () => {
    if (!window.confirm("Are you sure you want to delete this meeting? This action cannot be undone.")) return;

    setIsDeleting(true);
    try {
      const res = await fetch(`http://localhost:8000/api/meetings/${id}`, {
        method: 'DELETE',
      });
      if (res.ok) {
        navigate('/');
      } else {
        alert("Failed to delete meeting.");
        setIsDeleting(false);
      }
    } catch (err) {
      console.error(err);
      alert("Error occurred while deleting.");
      setIsDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Loader2 className="w-8 h-8 text-primary animate-spin" />
      </div>
    );
  }

  if (!meeting) {
    return <div className="text-center text-red-400 mt-20">Meeting not found.</div>;
  }

  // If still processing (no summary yet)
  const isProcessing = !meeting.summary && !meeting.transcript;

  return (
    <div className="max-w-5xl mx-auto space-y-8 animate-fade-in-up duration-500 pb-12">
      <Link to="/" className="inline-flex items-center text-black-400 hover:text-black transition-colors">
        <ArrowLeft className="w-4 h-4 mr-2" />
        Back to Dashboard
      </Link>

      <header className="glass p-8 rounded-3xl relative overflow-hidden border border-black/10">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/20 rounded-full blur-[80px] pointer-events-none"></div>
        <div className="relative z-10 flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold tracking-tight text-black mb-2">{meeting.title}</h1>
            <div className="flex items-center text-black-400">
              <Calendar className="w-4 h-4 mr-2" />
              {new Date(meeting.date).toLocaleDateString()}
            </div>
          </div>
          <div className="flex items-center space-x-3">
            {isProcessing && (
              <div className="flex flex-col items-end">
                <div className="px-4 py-2 bg-indigo-500/20 text-indigo-300 rounded-full text-sm font-medium border border-indigo-500/30 flex items-center">
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Processing Audio & Generating Summary...
                </div>
                <span className="text-xs text-black-500 mt-2">
                  (Check your backend terminal for real-time logs. Page will auto-refresh.)
                </span>
              </div>
            )}
            <button
              id="delete-meeting-btn"
              onClick={handleDelete}
              disabled={isDeleting}
              className="p-2 bg-red-500/10 text-red-400 hover:bg-red-500/20 rounded-xl transition-colors border border-red-500/20 flex items-center"
              title="Delete Meeting"
            >
              {isDeleting ? <Loader2 className="w-5 h-5 animate-spin" /> : <Trash2 className="w-5 h-5" />}
            </button>
          </div>
        </div>
      </header>

      {!isProcessing && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main content - Summary & Transcript */}
          <div className="lg:col-span-2 space-y-8">
            <section className="bg-white p-8 rounded-3xl border border-black/10">
              <h2 className="text-xl font-semibold mb-4 flex items-center text-black">
                <FileText className="w-5 h-5 mr-2 text-primary" />
                Executive Summary
              </h2>
              <div className="prose prose-invert max-w-none text-black-300 leading-relaxed">
                <p>{meeting.summary || "No summary available."}</p>
              </div>
            </section>

            <section className="bg-white p-8 rounded-3xl border border-black/10">
              <h2 className="text-xl font-semibold mb-4 text-black">Full Transcript</h2>
              <div className="bg-white/30 p-6 rounded-2xl max-h-96 overflow-y-auto text-black-400 text-sm leading-loose border border-black/10">
                {meeting.transcript || "No transcript available."}
              </div>
            </section>
          </div>

          {/* Sidebar - Action Items & Issues */}
          <div className="space-y-8">
            <section className="bg-white p-6 rounded-3xl border border-black/10 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-green-500/10 rounded-full blur-[40px] pointer-events-none"></div>
              <h2 className="text-lg font-semibold mb-4 flex items-center text-black relative z-10">
                <CheckCircle className="w-5 h-5 mr-2 text-green-400" />
                Action Items
              </h2>
              {meeting.action_items.length === 0 ? (
                <p className="text-black-500 text-sm">No action items detected.</p>
              ) : (
                <ul className="space-y-4 relative z-10">
                  {meeting.action_items.map(item => (
                    <li key={item.id} className="bg-white/5 p-4 rounded-xl border border-black/10">
                      <p className="font-medium text-black text-sm mb-1">{item.task}</p>
                      <div className="flex justify-between text-xs text-black-400 mt-2">
                        <span>Assignee: <span className="text-black-300">{item.owner || 'Unassigned'}</span></span>
                        <span className="px-2 py-0.5 rounded bg-white/10">{item.status}</span>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </section>

            <section className="bg-white p-6 rounded-3xl border border-black/10 relative overflow-hidden">
              <div className="absolute top-0 right-0 w-32 h-32 bg-red-500/10 rounded-full blur-[40px] pointer-events-none"></div>
              <h2 className="text-lg font-semibold mb-4 flex items-center text-black relative z-10">
                <AlertTriangle className="w-5 h-5 mr-2 text-red-400" />
                Issues & Risks
              </h2>
              {meeting.issues.length === 0 ? (
                <p className="text-black-500 text-sm">No issues detected.</p>
              ) : (
                <ul className="space-y-4 relative z-10">
                  {meeting.issues.map(issue => (
                    <li key={issue.id} className="bg-white/5 p-4 rounded-xl border border-red-500/10 border-l-2 border-l-red-500">
                      <p className="font-medium text-black text-sm mb-1">{issue.problem}</p>
                      {issue.product && <p className="text-xs text-black-400 mb-2">Product: {issue.product}</p>}
                      {issue.solution && (
                        <div className="mt-2 bg-white/20 p-2 rounded text-xs text-green-300 border border-green-500/10">
                          <span className="font-semibold block mb-0.5 text-green-400">Proposed Solution:</span>
                          {issue.solution}
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </section>
          </div>
        </div>
      )}
    </div>
  );
}
