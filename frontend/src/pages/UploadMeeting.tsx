import { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { UploadCloud, FileAudio, AlertCircle, Loader2 } from 'lucide-react';

export default function UploadMeeting() {
  const [title, setTitle] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);
  const navigate = useNavigate();
  const [sttModel, setSttModel] = useState('faster-whisper-large-v3');
  const [ensemble, setEnsemble] = useState(false);

  const handleUpload = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (!file || !title) return;

    setUploading(true);
    setError('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`http://localhost:8000/api/meetings/upload?title=${encodeURIComponent(title)}&stt_model=${encodeURIComponent(sttModel)}&ensemble=${ensemble}`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');
      
      const data = await response.json();
      // Wait a moment for background processing to start, then navigate
      setTimeout(() => navigate(`/meetings/${data.meeting_id}`), 1000);
    } catch (err) {
      console.error(err);
      setError('Failed to upload meeting. Please try again.');
      setUploading(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <header className="text-center">
        <h1 className="text-4xl font-bold tracking-tight mb-3 text-white">Upload Meeting</h1>
        <p className="text-gray-400">Upload your audio file to automatically generate minutes and action items.</p>
      </header>

      <form onSubmit={handleUpload} className="glass-dark p-8 rounded-3xl border border-white/10 shadow-2xl relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/10 rounded-full blur-[80px] pointer-events-none"></div>
        
        {error && (
          <div className="mb-6 p-4 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center text-red-400">
            <AlertCircle className="w-5 h-5 mr-3 flex-shrink-0" />
            <p>{error}</p>
          </div>
        )}

        <div className="space-y-6 relative z-10">
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Meeting Title</label>
            <input 
              type="text" 
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all"
              placeholder="e.g. Q3 Planning Meeting"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Speech-to-Text Model</label>
            <select
              name="stt_model"
              id="stt_model"
              value={sttModel}
              onChange={(e) => setSttModel(e.target.value)}
              className="w-full bg-black/40 border border-white/10 rounded-xl px-4 py-3 text-white focus:outline-none focus:ring-2 focus:ring-primary/50 focus:border-primary transition-all appearance-none"
            >
              <option value="faster-whisper-large-v3">Faster Whisper (Large-v3 - Best Quality)</option>
              <option value="faster-whisper-turbo">Faster Whisper (Turbo - Fast & Good)</option>
              <option value="thonburian">Thonburian Whisper (Thai Optimized)</option>
            </select>
          </div>

          <div className="flex items-center space-x-3 bg-black/20 p-4 rounded-xl border border-white/5">
            <input
              type="checkbox"
              id="ensemble"
              checked={ensemble}
              onChange={(e) => setEnsemble(e.target.checked)}
              className="w-5 h-5 rounded border-gray-400 text-primary focus:ring-primary focus:ring-offset-gray-900 bg-black/40"
            />
            <label htmlFor="ensemble" className="text-sm font-medium text-gray-300">
              Enable Ensemble Mode (Run model 3 times and LLM picks the best result - Slower)
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-300 mb-2">Audio File (MP3, WAV, M4A)</label>
            <div 
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition-all ${
                file ? 'border-primary/50 bg-primary/5' : 'border-white/20 hover:border-white/40 hover:bg-white/5'
              }`}
            >
              <input 
                type="file" 
                ref={fileInputRef}
                className="hidden" 
                accept="audio/mp3,audio/wav,audio/x-m4a,audio/*"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
              
              {file ? (
                <div className="flex flex-col items-center animate-in zoom-in duration-300">
                  <div className="w-16 h-16 bg-primary/20 rounded-full flex items-center justify-center mb-4">
                    <FileAudio className="w-8 h-8 text-primary" />
                  </div>
                  <p className="font-medium text-white mb-1">{file.name}</p>
                  <p className="text-xs text-gray-400">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                  <button 
                    type="button" 
                    onClick={(e) => { e.stopPropagation(); setFile(null); }}
                    className="mt-4 text-sm text-secondary hover:text-pink-400 transition-colors"
                  >
                    Remove File
                  </button>
                </div>
              ) : (
                <div className="flex flex-col items-center">
                  <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mb-4">
                    <UploadCloud className="w-8 h-8 text-gray-400" />
                  </div>
                  <p className="font-medium text-white mb-1">Click to browse or drag file here</p>
                  <p className="text-xs text-gray-500">Supports MP3, WAV, M4A up to 50MB</p>
                </div>
              )}
            </div>
          </div>

          <button 
            type="submit"
            disabled={!file || !title || uploading}
            className={`w-full py-4 rounded-xl font-medium text-lg flex items-center justify-center transition-all ${
              (!file || !title || uploading) 
                ? 'bg-white/10 text-gray-500 cursor-not-allowed' 
                : 'bg-gradient-to-r from-primary to-indigo-600 hover:from-indigo-500 hover:to-primary text-white shadow-lg shadow-primary/25 transform hover:-translate-y-0.5'
            }`}
          >
            {uploading ? (
              <>
                <Loader2 className="w-5 h-5 mr-3 animate-spin" />
                Uploading & Processing...
              </>
            ) : 'Upload and Analyze'}
          </button>
        </div>
      </form>
    </div>
  );
}
