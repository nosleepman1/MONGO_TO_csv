import React, { useState, useEffect } from "react"
import { 
  Database, 
  Download, 
  Cloud, 
  Calendar, 
  Trash2, 
  Clock, 
  AlertTriangle, 
  RefreshCw, 
  Info,
  Server
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { toast } from "sonner"
import API from "@/api/api"
import { Spinner } from "@/components/ui/spinner"

// Local types definition
type CloudProvider = 's3' | 'dropbox' | 'gdrive' | 'mock';

interface JobArgs {
  db_name: string;
  collection_name: string;
  provider: CloudProvider;
  dest_path: string;
}

interface Job {
  id: string;
  next_run_time: string | null;
  cron_expression: string;
  args: JobArgs;
}

const Home = () => {
  // Connection state
  const [connectionType, setConnectionType] = useState<"uri" | "details">("uri")
  const [uri, setUri] = useState("")
  const [cluster, setCluster] = useState("")
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [db, setDb] = useState("")
  const [collection, setCollection] = useState("")

  // Operation States
  const [activeTab, setActiveTab] = useState<"export" | "backup" | "schedule">("export")
  const [loading, setLoading] = useState(false)

  // Cloud Configs
  const [provider, setProvider] = useState<CloudProvider>("mock")
  const [destPath, setDestPath] = useState("backups/mongodb_export.csv")
  
  // Specific Provider Configs
  const [s3Bucket, setS3Bucket] = useState("")
  const [s3AccessKey, setS3AccessKey] = useState("")
  const [s3SecretKey, setS3SecretKey] = useState("")
  const [s3Region, setS3Region] = useState("")

  const [dbxToken, setDbxToken] = useState("")

  const [gdriveFolder, setGdriveFolder] = useState("")
  const [gdriveCredsFile, setGdriveCredsFile] = useState("")

  // Scheduler Job State
  const [jobId, setJobId] = useState("")
  const [cronExpression, setCronExpression] = useState("0 2 * * *")

  // Background state (jobs & scheduler status)
  const [jobs, setJobs] = useState<Job[]>([])
  const [schedulerRunning, setSchedulerRunning] = useState(false)
  const [fetchingJobs, setFetchingJobs] = useState(false)

  // Fetch scheduled jobs and status
  const fetchSchedulerData = async () => {
    setFetchingJobs(true)
    try {
      const statusRes = await API.get("/api/scheduler/status")
      if (statusRes.data && statusRes.data.status === "success") {
        setSchedulerRunning(statusRes.data.running)
      }

      const jobsRes = await API.get("/api/scheduler/jobs")
      if (jobsRes.data && jobsRes.data.status === "success") {
        setJobs(jobsRes.data.jobs || [])
      }
    } catch (err: any) {
      console.error(err)
      toast.error("Impossible de récupérer les tâches planifiées.")
    } finally {
      setFetchingJobs(false)
    }
  }

  useEffect(() => {
    fetchSchedulerData()
  }, [])

  // Auto-fill destination path when collection changes
  useEffect(() => {
    if (collection) {
      setDestPath(`backups/${collection}_export.csv`)
      setJobId(`backup-${collection}-daily`)
    }
  }, [collection])

  const getMongoDetails = () => {
    if (connectionType === "uri") {
      return { uri, db, collection }
    } else {
      return { cluster, username, password, db, collection }
    }
  }

  // Operation: Export direct CSV
  const handleExportCSV = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!db || !collection) {
      toast.error("Le nom de la base et de la collection sont requis.")
      return
    }

    setLoading(true)
    const toastId = toast.loading("Connexion et export des données en cours...")

    try {
      const payload = getMongoDetails()
      const response = await API.post("/export-csv", payload, {
        responseType: "blob", // Important for downloading files
      })

      // Extract filename from headers if possible
      let filename = `${collection}_export.csv`
      const disposition = response.headers["content-disposition"]
      if (disposition && disposition.includes("filename=")) {
        const matches = disposition.match(/filename="?([^"]+)"?/)
        if (matches && matches[1]) {
          filename = matches[1]
        }
      }

      // Download file in browser
      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement("a")
      link.href = url
      link.setAttribute("download", filename)
      document.body.appendChild(link)
      link.click()
      link.remove()
      window.URL.revokeObjectURL(url)

      toast.success("Export CSV téléchargé avec succès !", { id: toastId })
    } catch (err: any) {
      console.error(err)
      // Decode blob error message if returned as json
      if (err.response?.data instanceof Blob) {
        const reader = new FileReader()
        reader.onload = () => {
          try {
            const errorMsg = JSON.parse(reader.result as string)
            toast.error(`Erreur: ${errorMsg.detail || "Inconnue"}`, { id: toastId })
          } catch {
            toast.error("Échec de l'export. Vérifiez la connexion MongoDB.", { id: toastId })
          }
        }
        reader.readAsText(err.response.data)
      } else {
        toast.error(
          err.response?.data?.detail || "Échec de l'export. Vérifiez la connexion MongoDB.", 
          { id: toastId }
        )
      }
    } finally {
      setLoading(false)
    }
  }

  // Get Cloud Provider configurations object
  const getProviderConfig = () => {
    const config: any = {}
    if (provider === "s3") {
      if (s3Bucket) config.bucket_name = s3Bucket
      if (s3AccessKey) config.aws_access_key_id = s3AccessKey
      if (s3SecretKey) config.aws_secret_access_key = s3SecretKey
      if (s3Region) config.region_name = s3Region
    } else if (provider === "dropbox") {
      if (dbxToken) config.access_token = dbxToken
    } else if (provider === "gdrive") {
      if (gdriveFolder) config.folder_id = gdriveFolder
      if (gdriveCredsFile) config.credentials_file = gdriveCredsFile
    }
    return config
  }

  // Operation: Immediate backup to cloud
  const handleImmediateBackup = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!db || !collection) {
      toast.error("Le nom de la base et de la collection sont requis.")
      return
    }

    setLoading(true)
    const toastId = toast.loading(`Sauvegarde en cours vers ${provider.toUpperCase()}...`)

    try {
      const payload = {
        ...getMongoDetails(),
        provider,
        dest_path: destPath,
        provider_config: getProviderConfig()
      }

      const response = await API.post("/api/backup", payload)
      if (response.data && response.data.status === "success") {
        toast.success(response.data.message || "Sauvegarde effectuée avec succès !", { id: toastId })
      } else {
        toast.error("Une erreur s'est produite lors de la sauvegarde.", { id: toastId })
      }
    } catch (err: any) {
      console.error(err)
      toast.error(err.response?.data?.detail || "Échec du téléversement Cloud.", { id: toastId })
    } finally {
      setLoading(false)
    }
  }

  // Operation: Schedule a backup
  const handleScheduleBackup = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!db || !collection || !jobId || !cronExpression) {
      toast.error("La DB, la Collection, l'ID de la tâche et l'expression Cron sont requis.")
      return
    }

    setLoading(true)
    const toastId = toast.loading(`Planification de la tâche '${jobId}'...`)

    try {
      const payload = {
        ...getMongoDetails(),
        job_id: jobId,
        cron_expression: cronExpression,
        provider,
        dest_path: destPath,
        provider_config: getProviderConfig()
      }

      const response = await API.post("/api/scheduler/jobs", payload)
      if (response.data && response.data.status === "success") {
        toast.success(response.data.message || "Tâche planifiée avec succès !", { id: toastId })
        fetchSchedulerData() // Refresh table
      } else {
        toast.error("Erreur lors de la planification de la tâche.", { id: toastId })
      }
    } catch (err: any) {
      console.error(err)
      toast.error(err.response?.data?.detail || "Échec de la planification de la tâche.", { id: toastId })
    } finally {
      setLoading(false)
    }
  }

  // Action: Delete a scheduled job
  const handleDeleteJob = async (id: string) => {
    const toastId = toast.loading(`Suppression de la tâche '${id}'...`)
    try {
      const response = await API.delete(`/api/scheduler/jobs/${id}`)
      if (response.data && response.data.status === "success") {
        toast.success(`Tâche '${id}' supprimée avec succès.`, { id: toastId })
        fetchSchedulerData()
      } else {
        toast.error("Impossible de supprimer la tâche.", { id: toastId })
      }
    } catch (err: any) {
      console.error(err)
      toast.error(err.response?.data?.detail || "Erreur lors de la suppression.", { id: toastId })
    }
  }

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* Introduction Card */}
      <div className="bg-gradient-to-r from-indigo-900 via-indigo-950 to-slate-900 rounded-2xl p-6 text-white shadow-xl flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold flex items-center gap-2">
            Tableau de Bord Backups <span className="text-xs bg-indigo-600 text-indigo-100 font-bold px-2 py-0.5 rounded-full uppercase tracking-wider">v1.1.0</span>
          </h1>
          <p className="text-indigo-200 mt-2 max-w-xl text-sm leading-relaxed">
            Connectez-vous à vos instances MongoDB (locales ou Atlas), générez des fichiers CSV nettoyés instantanément et planifiez des sauvegardes automatiques vers AWS S3, Dropbox ou Google Drive.
          </p>
        </div>
        <div className="flex items-center gap-3 bg-white/10 px-4 py-3 rounded-xl backdrop-blur-sm self-stretch md:self-auto justify-between">
          <div className="flex items-center gap-2 text-sm font-medium">
            <Server className="w-4 h-4 text-emerald-400" />
            <span>Statut Planificateur :</span>
          </div>
          <Badge className={schedulerRunning ? "bg-emerald-500 text-emerald-950 font-bold" : "bg-amber-500 text-amber-950 font-bold"}>
            {schedulerRunning ? "ACTIF" : "INACTIF"}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Left Side: MongoDB Connection Configuration */}
        <div className="lg:col-span-5 space-y-6">
          <Card className="shadow-lg border-slate-200/60 overflow-hidden">
            <div className="bg-gradient-to-r from-slate-900 to-slate-950 text-white p-4">
              <CardTitle className="text-base font-bold flex items-center gap-2">
                <Database className="w-4 h-4 text-indigo-400" />
                1. Connexion MongoDB
              </CardTitle>
              <CardDescription className="text-slate-400 text-xs mt-1">
                Configurez les identifiants d'accès à la collection cible.
              </CardDescription>
            </div>
            
            <CardContent className="pt-6 space-y-4">
              {/* Connection Type Selector */}
              <div className="flex p-0.5 bg-slate-100 rounded-lg font-sans">
                <button
                  type="button"
                  onClick={() => setConnectionType("uri")}
                  className={`flex-1 text-center py-2 text-xs font-semibold rounded-md transition-all ${
                    connectionType === "uri" 
                      ? "bg-white text-indigo-950 shadow-sm" 
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  URI de connexion
                </button>
                <button
                  type="button"
                  onClick={() => setConnectionType("details")}
                  className={`flex-1 text-center py-2 text-xs font-semibold rounded-md transition-all ${
                    connectionType === "details" 
                      ? "bg-white text-indigo-950 shadow-sm" 
                      : "text-slate-600 hover:text-slate-900"
                  }`}
                >
                  Détails Atlas
                </button>
              </div>

              {connectionType === "uri" ? (
                <div className="space-y-2">
                  <Label htmlFor="uri" className="text-xs font-bold text-slate-700">URI MongoDB</Label>
                  <Input
                    id="uri"
                    placeholder="mongodb+srv://admin:pwd@cluster.mongodb.net/ ou mongodb://localhost:27017/"
                    value={uri}
                    onChange={(e) => setUri(e.target.value)}
                    className="text-xs"
                  />
                  <p className="text-[10px] text-slate-500 flex items-start gap-1">
                    <Info className="w-3.5 h-3.5 inline mt-0.5 text-indigo-500 shrink-0" />
                    <span>L'URI prend le dessus sur les autres paramètres de connexion.</span>
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  <div className="space-y-1.5">
                    <Label htmlFor="cluster" className="text-xs font-bold text-slate-700">Cluster Hostname</Label>
                    <Input
                      id="cluster"
                      placeholder="cluster0.vvtqpfm"
                      value={cluster}
                      onChange={(e) => setCluster(e.target.value)}
                      className="text-xs"
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="space-y-1.5">
                      <Label htmlFor="username" className="text-xs font-bold text-slate-700">Nom d'utilisateur</Label>
                      <Input
                        id="username"
                        placeholder="admin"
                        value={username}
                        onChange={(e) => setUsername(e.target.value)}
                        className="text-xs"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="password" className="text-xs font-bold text-slate-700">Mot de passe</Label>
                      <Input
                        id="password"
                        type="password"
                        placeholder="••••••••"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="text-xs"
                      />
                    </div>
                  </div>
                </div>
              )}

              <hr className="border-slate-100" />

              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <Label htmlFor="db" className="text-xs font-bold text-slate-700">Base de données <span className="text-red-500">*</span></Label>
                  <Input
                    id="db"
                    placeholder="my_database"
                    required
                    value={db}
                    onChange={(e) => setDb(e.target.value)}
                    className="text-xs font-medium"
                  />
                </div>
                <div className="space-y-1.5">
                  <Label htmlFor="collection" className="text-xs font-bold text-slate-700">Collection <span className="text-red-500">*</span></Label>
                  <Input
                    id="collection"
                    placeholder="users"
                    required
                    value={collection}
                    onChange={(e) => setCollection(e.target.value)}
                    className="text-xs font-medium"
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right Side: Operations Panel */}
        <div className="lg:col-span-7 space-y-6">
          <Card className="shadow-lg border-slate-200/60 min-h-[380px] flex flex-col">
            <div className="border-b border-slate-100 bg-slate-50/50 p-2 flex gap-1">
              <button
                onClick={() => setActiveTab("export")}
                className={`flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-bold rounded-lg transition-all ${
                  activeTab === "export"
                    ? "bg-white text-indigo-600 shadow-sm border border-slate-200/60"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <Download className="w-3.5 h-3.5" />
                Export CSV Direct
              </button>
              <button
                onClick={() => setActiveTab("backup")}
                className={`flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-bold rounded-lg transition-all ${
                  activeTab === "backup"
                    ? "bg-white text-indigo-600 shadow-sm border border-slate-200/60"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <Cloud className="w-3.5 h-3.5" />
                Sauvegarde Cloud
              </button>
              <button
                onClick={() => setActiveTab("schedule")}
                className={`flex-1 flex items-center justify-center gap-1.5 py-3 text-xs font-bold rounded-lg transition-all ${
                  activeTab === "schedule"
                    ? "bg-white text-indigo-600 shadow-sm border border-slate-200/60"
                    : "text-slate-600 hover:text-slate-900"
                }`}
              >
                <Calendar className="w-3.5 h-3.5" />
                Planificateur Cron
              </button>
            </div>

            <CardContent className="pt-6 flex-1">
              {/* TAB 1: Export CSV */}
              {activeTab === "export" && (
                <form onSubmit={handleExportCSV} className="space-y-6">
                  <div className="bg-blue-50/60 border border-blue-100 text-blue-800 rounded-xl p-4 text-xs space-y-1.5 leading-relaxed">
                    <h4 className="font-bold flex items-center gap-1">
                      <Info className="w-4 h-4 text-blue-500" />
                      Comment fonctionne l'export ?
                    </h4>
                    <p>Le backend FastAPI va se connecter à votre collection MongoDB, normaliser les données en aplatissant les structures imbriquées (nested JSON), convertir les listes et générer un fichier CSV propre prêt au téléchargement.</p>
                  </div>

                  <div className="flex flex-col gap-2">
                    <Button 
                      type="submit" 
                      disabled={loading || !db || !collection}
                      className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-5 rounded-xl shadow-md shadow-indigo-100 flex items-center justify-center gap-2"
                    >
                      {loading ? (
                        <>
                          <Spinner className="w-4 h-4 text-white animate-spin" />
                          Traitement des données...
                        </>
                      ) : (
                        <>
                          <Download className="w-4 h-4" />
                          Générer et Télécharger le CSV
                        </>
                      )}
                    </Button>
                  </div>
                </form>
              )}

              {/* TAB 2: Sauvegarde Cloud Immédiate */}
              {activeTab === "backup" && (
                <form onSubmit={handleImmediateBackup} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <Label htmlFor="provider" className="text-xs font-bold text-slate-700">Stockage Cloud</Label>
                      <Select 
                        value={provider} 
                        onValueChange={(val) => setProvider(val as CloudProvider)}
                      >
                        <SelectTrigger className="text-xs">
                          <SelectValue placeholder="Sélectionnez un provider" />
                        </SelectTrigger>
                        <SelectContent className="text-xs">
                          <SelectItem value="mock">Dossier Local (Mock)</SelectItem>
                          <SelectItem value="s3">AWS S3</SelectItem>
                          <SelectItem value="dropbox">Dropbox</SelectItem>
                          <SelectItem value="gdrive">Google Drive</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="destPath" className="text-xs font-bold text-slate-700">Chemin de destination</Label>
                      <Input
                        id="destPath"
                        placeholder="backups/users_export.csv"
                        value={destPath}
                        onChange={(e) => setDestPath(e.target.value)}
                        className="text-xs"
                      />
                    </div>
                  </div>

                  {/* Provider Specific Inputs */}
                  {provider === "mock" && (
                    <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl text-xs text-slate-600">
                      ℹ️ Sauvegarde enregistrée localement dans le dossier <code>backend/mock_uploads/</code>.
                    </div>
                  )}

                  {provider === "s3" && (
                    <div className="p-4 bg-slate-50 border border-slate-100 rounded-xl space-y-3">
                      <h4 className="text-xs font-bold text-slate-700">Configuration AWS S3 (Optionnelle si définie en .env)</h4>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label htmlFor="s3Bucket" className="text-[10px] font-bold text-slate-500">Nom du Bucket <span className="text-red-500">*</span></Label>
                          <Input id="s3Bucket" placeholder="my-bucket-name" value={s3Bucket} onChange={(e) => setS3Bucket(e.target.value)} className="h-8 text-xs" />
                        </div>
                        <div className="space-y-1">
                          <Label htmlFor="s3Region" className="text-[10px] font-bold text-slate-500">Région AWS</Label>
                          <Input id="s3Region" placeholder="eu-west-3" value={s3Region} onChange={(e) => setS3Region(e.target.value)} className="h-8 text-xs" />
                        </div>
                      </div>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label htmlFor="s3AccessKey" className="text-[10px] font-bold text-slate-500">AWS Access Key ID</Label>
                          <Input id="s3AccessKey" type="password" placeholder="AKIA..." value={s3AccessKey} onChange={(e) => setS3AccessKey(e.target.value)} className="h-8 text-xs" />
                        </div>
                        <div className="space-y-1">
                          <Label htmlFor="s3SecretKey" className="text-[10px] font-bold text-slate-500">AWS Secret Access Key</Label>
                          <Input id="s3SecretKey" type="password" placeholder="wJal..." value={s3SecretKey} onChange={(e) => setS3SecretKey(e.target.value)} className="h-8 text-xs" />
                        </div>
                      </div>
                    </div>
                  )}

                  {provider === "dropbox" && (
                    <div className="p-4 bg-slate-50 border border-slate-100 rounded-xl space-y-2">
                      <h4 className="text-xs font-bold text-slate-700">Configuration Dropbox (Optionnelle si définie en .env)</h4>
                      <div className="space-y-1">
                        <Label htmlFor="dbxToken" className="text-[10px] font-bold text-slate-500">Access Token Dropbox</Label>
                        <Input id="dbxToken" type="password" placeholder="sl.B..." value={dbxToken} onChange={(e) => setDbxToken(e.target.value)} className="h-8 text-xs" />
                      </div>
                    </div>
                  )}

                  {provider === "gdrive" && (
                    <div className="p-4 bg-slate-50 border border-slate-100 rounded-xl space-y-3">
                      <h4 className="text-xs font-bold text-slate-700">Configuration Google Drive (Optionnelle si définie en .env)</h4>
                      <div className="grid grid-cols-2 gap-3">
                        <div className="space-y-1">
                          <Label htmlFor="gdriveFolder" className="text-[10px] font-bold text-slate-500">Folder ID Google Drive</Label>
                          <Input id="gdriveFolder" placeholder="1A2B3C..." value={gdriveFolder} onChange={(e) => setGdriveFolder(e.target.value)} className="h-8 text-xs" />
                        </div>
                        <div className="space-y-1">
                          <Label htmlFor="gdriveCredsFile" className="text-[10px] font-bold text-slate-500">Fichier de credentials (ex: credentials.json)</Label>
                          <Input id="gdriveCredsFile" placeholder="credentials.json" value={gdriveCredsFile} onChange={(e) => setGdriveCredsFile(e.target.value)} className="h-8 text-xs" />
                        </div>
                      </div>
                    </div>
                  )}

                  <Button 
                    type="submit" 
                    disabled={loading || !db || !collection}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-4 rounded-xl shadow-md shadow-indigo-100 flex items-center justify-center gap-2 mt-4"
                  >
                    {loading ? (
                      <>
                        <Spinner className="w-4 h-4 text-white animate-spin" />
                        Téléversement en cours...
                      </>
                    ) : (
                      <>
                        <Cloud className="w-4 h-4" />
                        Sauvegarder vers le Cloud maintenant
                      </>
                    )}
                  </Button>
                </form>
              )}

              {/* TAB 3: Planifier une Sauvegarde */}
              {activeTab === "schedule" && (
                <form onSubmit={handleScheduleBackup} className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <Label htmlFor="jobId" className="text-xs font-bold text-slate-700">ID de la tâche (Unique) <span className="text-red-500">*</span></Label>
                      <Input
                        id="jobId"
                        placeholder="daily-users-backup"
                        value={jobId}
                        onChange={(e) => setJobId(e.target.value)}
                        className="text-xs"
                      />
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="cronExpression" className="text-xs font-bold text-slate-700">Expression Cron <span className="text-red-500">*</span></Label>
                      <Input
                        id="cronExpression"
                        placeholder="0 2 * * *"
                        value={cronExpression}
                        onChange={(e) => setCronExpression(e.target.value)}
                        className="text-xs"
                      />
                    </div>
                  </div>

                  {/* Quick cron presets */}
                  <div className="flex gap-2">
                    <span className="text-[10px] font-bold text-slate-500 self-center">Raccourcis Cron :</span>
                    <button
                      type="button"
                      onClick={() => setCronExpression("0 * * * *")}
                      className="px-2 py-1 text-[10px] bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md font-semibold border border-slate-200/60 transition-all"
                    >
                      Toutes les heures
                    </button>
                    <button
                      type="button"
                      onClick={() => setCronExpression("0 2 * * *")}
                      className="px-2 py-1 text-[10px] bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md font-semibold border border-slate-200/60 transition-all"
                    >
                      Tous les jours à 2h
                    </button>
                    <button
                      type="button"
                      onClick={() => setCronExpression("0 0 * * 0")}
                      className="px-2 py-1 text-[10px] bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-md font-semibold border border-slate-200/60 transition-all"
                    >
                      Chaque dimanche
                    </button>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1.5">
                      <Label htmlFor="scheduleProvider" className="text-xs font-bold text-slate-700">Stockage Cloud</Label>
                      <Select 
                        value={provider} 
                        onValueChange={(val) => setProvider(val as CloudProvider)}
                      >
                        <SelectTrigger className="text-xs">
                          <SelectValue placeholder="Sélectionnez un provider" />
                        </SelectTrigger>
                        <SelectContent className="text-xs">
                          <SelectItem value="mock">Dossier Local (Mock)</SelectItem>
                          <SelectItem value="s3">AWS S3</SelectItem>
                          <SelectItem value="dropbox">Dropbox</SelectItem>
                          <SelectItem value="gdrive">Google Drive</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                    <div className="space-y-1.5">
                      <Label htmlFor="scheduleDestPath" className="text-xs font-bold text-slate-700">Chemin de destination</Label>
                      <Input
                        id="scheduleDestPath"
                        placeholder="backups/users_export.csv"
                        value={destPath}
                        onChange={(e) => setDestPath(e.target.value)}
                        className="text-xs"
                      />
                    </div>
                  </div>

                  {/* Provider Settings collapse/section similar to direct upload */}
                  {provider === "s3" && (
                    <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl space-y-2">
                      <div className="grid grid-cols-2 gap-2">
                        <Input id="s3Bucket" placeholder="Bucket AWS" value={s3Bucket} onChange={(e) => setS3Bucket(e.target.value)} className="h-8 text-xs" />
                        <Input id="s3Region" placeholder="Région AWS" value={s3Region} onChange={(e) => setS3Region(e.target.value)} className="h-8 text-xs" />
                      </div>
                    </div>
                  )}

                  {provider === "dropbox" && (
                    <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl">
                      <Input id="dbxToken" type="password" placeholder="Access Token Dropbox" value={dbxToken} onChange={(e) => setDbxToken(e.target.value)} className="h-8 text-xs" />
                    </div>
                  )}

                  {provider === "gdrive" && (
                    <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl space-y-2">
                      <div className="grid grid-cols-2 gap-2">
                        <Input id="gdriveFolder" placeholder="Folder ID GDrive" value={gdriveFolder} onChange={(e) => setGdriveFolder(e.target.value)} className="h-8 text-xs" />
                        <Input id="gdriveCredsFile" placeholder="credentials.json" value={gdriveCredsFile} onChange={(e) => setGdriveCredsFile(e.target.value)} className="h-8 text-xs" />
                      </div>
                    </div>
                  )}

                  <Button 
                    type="submit" 
                    disabled={loading || !db || !collection || !jobId || !cronExpression}
                    className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-bold py-4 rounded-xl shadow-md shadow-indigo-100 flex items-center justify-center gap-2 mt-4"
                  >
                    {loading ? (
                      <>
                        <Spinner className="w-4 h-4 text-white animate-spin" />
                        Enregistrement...
                      </>
                    ) : (
                      <>
                        <Calendar className="w-4 h-4" />
                        Planifier la sauvegarde automatique
                      </>
                    )}
                  </Button>
                </form>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Section: active scheduled jobs */}
      <Card className="shadow-lg border-slate-200/60 overflow-hidden">
        <div className="bg-gradient-to-r from-slate-900 to-slate-950 text-white px-6 py-4 flex justify-between items-center">
          <div>
            <CardTitle className="text-base font-bold flex items-center gap-2">
              <Clock className="w-4 h-4 text-indigo-400" />
              Tâches actives planifiées ({jobs.length})
            </CardTitle>
            <CardDescription className="text-slate-400 text-xs mt-0.5">
              Visualisez et gérez toutes les sauvegardes planifiées récurrentes actives.
            </CardDescription>
          </div>
          <Button 
            variant="outline" 
            size="sm" 
            onClick={fetchSchedulerData} 
            className="h-8 bg-white/10 hover:bg-white/20 text-white border-white/20 text-xs font-semibold"
          >
            <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${fetchingJobs ? "animate-spin" : ""}`} />
            Actualiser
          </Button>
        </div>

        <CardContent className="p-0">
          {fetchingJobs && jobs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-400">
              <Spinner className="w-8 h-8 text-indigo-600 mb-3" />
              <p className="text-xs">Chargement des tâches planifiées...</p>
            </div>
          ) : jobs.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-slate-400 text-center px-4">
              <AlertTriangle className="w-8 h-8 text-slate-300 mb-2" />
              <p className="text-xs font-bold text-slate-600">Aucune tâche planifiée</p>
              <p className="text-[11px] text-slate-400 max-w-sm mt-1">Configurez le planificateur ci-dessus pour automatiser vos exports de données MongoDB.</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-left text-xs">
                <thead>
                  <tr className="bg-slate-50 border-b border-slate-200/80 text-slate-600 font-bold uppercase tracking-wider text-[10px]">
                    <th className="px-6 py-3.5">ID de la Tâche</th>
                    <th className="px-6 py-3.5">Cible MongoDB</th>
                    <th className="px-6 py-3.5">Cron / Fréquence</th>
                    <th className="px-6 py-3.5">Stockage & Destination</th>
                    <th className="px-6 py-3.5">Prochaine Exécution</th>
                    <th className="px-6 py-3.5 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700">
                  {jobs.map((job) => (
                    <tr key={job.id} className="hover:bg-slate-50/50 transition-all font-medium">
                      <td className="px-6 py-4">
                        <span className="font-bold text-slate-900 font-mono bg-slate-100 px-2 py-1 rounded border border-slate-200/60">
                          {job.id}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-col">
                          <span className="text-slate-900 font-bold">{job.args.db_name}</span>
                          <span className="text-[10px] text-slate-500 font-semibold font-mono">.{job.args.collection_name}</span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <span className="font-mono bg-indigo-50 text-indigo-700 border border-indigo-100 px-2 py-0.5 rounded font-bold">
                          {job.cron_expression.replace('cron[', '').replace(']', '')}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex flex-col">
                          <span className="text-[10px] font-extrabold uppercase text-indigo-600">{job.args.provider}</span>
                          <span className="text-[10px] text-slate-500 font-mono truncate max-w-[200px]" title={job.args.dest_path}>
                            {job.args.dest_path}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 font-mono text-slate-600 text-[11px]">
                        {job.next_run_time ? (
                          new Date(job.next_run_time).toLocaleString("fr-FR", {
                            dateStyle: "short",
                            timeStyle: "short"
                          })
                        ) : (
                          <span className="text-slate-400">Suspendu</span>
                        )}
                      </td>
                      <td className="px-6 py-4 text-right font-sans">
                        <Button
                          variant="destructive"
                          size="icon"
                          onClick={() => handleDeleteJob(job.id)}
                          className="h-8 w-8 hover:bg-red-600 text-white rounded-lg shadow-sm"
                          title="Supprimer la tâche"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default Home