import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Mic, Search, LayoutDashboard, Hexagon } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import UploadMeeting from './pages/UploadMeeting';
import MeetingDetails from './pages/MeetingDetails';
import SearchPage from './pages/Search';

function App() {
  return (
    <Router>

      <div className="flex h-screen overflow-hidden">
        {/* Sidebar - Changed background to a rich dark blue (bg-blue-950) */}
        <aside className="w-64 bg-blue-950 flex flex-col hidden md:flex border-r border-white/10 relative z-10 text-white">

          {/* Header Section - Wrapped in a flexcontainer to align the Hexagon horizontally */}
          <div className="p-6 flex items-center space-x-3">
            {/* Hexagon Shape added to the left */}
            <Hexagon className="w-8 h-8 text-white fill-white/10 shrink-0 animate-pulse" />
            <div>
              <h1 className="text-2xl font-bold text-white tracking-wide">
                DAD AI
              </h1>
              <p className="text-xs text-blue-200/80 mt-0.5">Meeting Intelligence</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex-1 px-4 space-y-2 mt-4">
            <Link to="/" className="flex items-center space-x-3 px-4 py-3 rounded-xl hover:bg-white/10 transition-all group">
              <LayoutDashboard className="w-5 h-5 text-white/60 group-hover:text-white transition-colors" />
              <span className="font-medium text-white/80 group-hover:text-white transition-colors">Dashboard</span>
            </Link>

            <Link to="/upload" className="flex items-center space-x-3 px-4 py-3 rounded-xl hover:bg-white/10 transition-all group">
              <Mic className="w-5 h-5 text-white/60 group-hover:text-white transition-colors" />
              <span className="font-medium text-white/80 group-hover:text-white transition-colors">Upload Meeting</span>
            </Link>

            <Link to="/search" className="flex items-center space-x-3 px-4 py-3 rounded-xl hover:bg-white/10 transition-all group">
              <Search className="w-5 h-5 text-white/60 group-hover:text-white transition-colors" />
              <span className="font-medium text-white/80 group-hover:text-white transition-colors">Search & Ask</span>
            </Link>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto relative bg-slate-50 text-slate-900">
          {/* Modernized background accents for light mode (adjusted opacity and removed mix-blend-screen) */}
          <div className="absolute top-0 left-0 w-full h-96 bg-blue-500/5 blur-[120px] rounded-full pointer-events-none -z-10 transform -translate-y-1/2"></div>
          <div className="absolute bottom-0 right-0 w-full h-96 bg-indigo-500/5 blur-[120px] rounded-full pointer-events-none -z-10 transform translate-y-1/2 translate-x-1/4"></div>

          <div className="p-8 max-w-7xl mx-auto h-full">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/upload" element={<UploadMeeting />} />
              <Route path="/meetings/:id" element={<MeetingDetails />} />
              <Route path="/search" element={<SearchPage />} />
            </Routes>
          </div>
        </main>
      </div>
    </Router>
  );
}

export default App;
