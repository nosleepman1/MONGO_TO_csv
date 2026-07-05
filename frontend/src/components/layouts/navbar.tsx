import { Database } from "lucide-react"

const Navbar = () => {
  return (
    <nav className="bg-white/80 backdrop-blur-md border-b border-slate-200 sticky top-0 z-50 px-6 py-4 flex justify-between items-center">
      <div className="flex items-center gap-2">
        <div className="bg-indigo-600 text-white p-2 rounded-lg shadow-md shadow-indigo-100 flex items-center justify-center">
          <Database className="w-5 h-5" />
        </div>
        <div>
          <span className="text-lg font-bold bg-gradient-to-r from-slate-900 to-indigo-950 bg-clip-text text-transparent">
            MongoDB ➔ CSV
          </span>
          <span className="text-xs font-semibold text-indigo-600 block leading-none">
            Backup & Scheduler
          </span>
        </div>
      </div>
      <div className="flex items-center gap-4">
        <span className="flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
          <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
          API Connectée
        </span>
      </div>
    </nav>
  )
}

export default Navbar