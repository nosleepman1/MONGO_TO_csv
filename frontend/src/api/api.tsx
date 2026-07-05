import axios from "axios"

const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000"

const API = axios.create({
    baseURL: API_URL,
    headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    },
})

// Request interceptor left simple as auth is disabled
API.interceptors.request.use(async (config) => {
    return config
}, (error) => {
    return Promise.reject(error)
})

export default API