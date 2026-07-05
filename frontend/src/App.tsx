import Navbar from "./components/layouts/navbar"
import AppRoutes from "./routes/appRoutes"
import { Toaster } from "@/components/ui/sonner"

const App = () => {
  return (
    <main className="min-h-screen bg-slate-50">
      <Navbar />
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <AppRoutes />
      </div>
      <Toaster position="bottom-right" richColors />
    </main>
  )
}

export default App