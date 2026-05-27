import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Mic, Search, LayoutDashboard } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import UploadMeeting from './pages/UploadMeeting';
import MeetingDetails from './pages/MeetingDetails';
import SearchPage from './pages/Search';

function App() {
  return (
    <Router>
      <div className="flex h-screen overflow-hidden">
        {/* Sidebar */}
        <aside className="w-64 glass-dark flex flex-col hidden md:flex border-r border-white/10 relative z-10">
          <div className="p-6">
            <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary">
              SmartConference
            </h1>
            <p className="text-sm text-gray-400 mt-1">AI Meeting Intelligence</p>
          </div>
          <nav className="flex-1 px-4 space-y-2 mt-4">
            <Link to="/" className="flex items-center space-x-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-all group">
              <LayoutDashboard className="w-5 h-5 text-gray-400 group-hover:text-primary transition-colors" />
              <span className="font-medium text-gray-300 group-hover:text-white transition-colors">Dashboard</span>
            </Link>
            <Link to="/upload" className="flex items-center space-x-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-all group">
              <Mic className="w-5 h-5 text-gray-400 group-hover:text-secondary transition-colors" />
              <span className="font-medium text-gray-300 group-hover:text-white transition-colors">Upload Meeting</span>
            </Link>
            <Link to="/search" className="flex items-center space-x-3 px-4 py-3 rounded-xl hover:bg-white/5 transition-all group">
              <Search className="w-5 h-5 text-gray-400 group-hover:text-primary transition-colors" />
              <span className="font-medium text-gray-300 group-hover:text-white transition-colors">Search & Ask</span>
            </Link>
          </nav>
        </aside>

        {/* Main Content */}
        <main className="flex-1 overflow-y-auto relative">
          <div className="absolute top-0 left-0 w-full h-96 bg-primary/20 blur-[120px] rounded-full pointer-events-none -z-10 mix-blend-screen transform -translate-y-1/2"></div>
          <div className="absolute bottom-0 right-0 w-full h-96 bg-secondary/10 blur-[120px] rounded-full pointer-events-none -z-10 mix-blend-screen transform translate-y-1/2 translate-x-1/4"></div>

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
