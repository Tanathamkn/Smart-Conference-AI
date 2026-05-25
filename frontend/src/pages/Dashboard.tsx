import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Calendar, ChevronRight, Users, CheckCircle, Clock } from 'lucide-react';

interface Meeting {
  id: number;
  title: string;
  date: string;
  summary: string;
}

export default function Dashboard() {
  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/api/meetings')
      .then(res => res.json())
      .then(data => {
        setMeetings(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Failed to fetch meetings", err);
        setLoading(false);
      });
  }, []);

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header>
        <h1 className="text-4xl font-bold tracking-tight mb-2 text-white">Dashboard</h1>
        <p className="text-gray-400">Welcome back. Here is your meeting overview.</p>
      </header>

      {/* Stats row */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="glass-dark p-6 rounded-2xl relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-r from-primary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-sm font-medium mb-1">Total Meetings</p>
              <h3 className="text-3xl font-bold text-white">{meetings.length}</h3>
            </div>
            <div className="bg-primary/20 p-3 rounded-xl">
              <Users className="w-6 h-6 text-primary" />
            </div>
          </div>
        </div>
        <div className="glass-dark p-6 rounded-2xl relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-r from-green-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-sm font-medium mb-1">Action Items</p>
              <h3 className="text-3xl font-bold text-white">12</h3>
            </div>
            <div className="bg-green-500/20 p-3 rounded-xl">
              <CheckCircle className="w-6 h-6 text-green-400" />
            </div>
          </div>
        </div>
        <div className="glass-dark p-6 rounded-2xl relative overflow-hidden group">
          <div className="absolute inset-0 bg-gradient-to-r from-secondary/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity"></div>
          <div className="flex justify-between items-start">
            <div>
              <p className="text-gray-400 text-sm font-medium mb-1">Hours Processed</p>
              <h3 className="text-3xl font-bold text-white">4.5</h3>
            </div>
            <div className="bg-secondary/20 p-3 rounded-xl">
              <Clock className="w-6 h-6 text-secondary" />
            </div>
          </div>
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4 text-white">Recent Meetings</h2>
        {loading ? (
          <div className="glass-dark rounded-2xl p-8 flex justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : meetings.length === 0 ? (
          <div className="glass-dark rounded-2xl p-12 text-center border border-dashed border-white/20">
            <p className="text-gray-400 mb-4">No meetings recorded yet.</p>
            <Link to="/upload" className="inline-flex items-center px-4 py-2 bg-primary hover:bg-indigo-600 transition-colors rounded-lg font-medium">
              Upload First Meeting
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {meetings.map((meeting) => (
              <Link 
                key={meeting.id} 
                to={`/meetings/${meeting.id}`}
                className="block glass-dark p-6 rounded-2xl hover:bg-white/[0.08] transition-all transform hover:-translate-y-1 border border-transparent hover:border-white/10 group"
              >
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-lg font-semibold text-white mb-1 group-hover:text-primary transition-colors">{meeting.title}</h3>
                    <div className="flex items-center text-sm text-gray-400">
                      <Calendar className="w-4 h-4 mr-2" />
                      {new Date(meeting.date).toLocaleDateString()}
                    </div>
                  </div>
                  <ChevronRight className="w-5 h-5 text-gray-500 group-hover:text-white transition-colors" />
                </div>
                {meeting.summary && (
                  <p className="mt-4 text-sm text-gray-400 line-clamp-2 leading-relaxed">
                    {meeting.summary}
                  </p>
                )}
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
