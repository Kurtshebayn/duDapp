import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from './auth/AuthContext'
import ProtectedRoute from './auth/ProtectedRoute'
import Nav from './components/Nav'
import ColdStartBanner from './components/ColdStartBanner'
import Ranking from './pages/Ranking'
import Reuniones from './pages/Reuniones'
import ReunionDetalle from './pages/ReunionDetalle'
import Estadisticas from './pages/Estadisticas'
import Login from './pages/Login'
import Dashboard from './pages/admin/Dashboard'
import CrearTemporada from './pages/admin/CrearTemporada'
import GestionReunion from './pages/admin/GestionReunion'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Nav />
        <ColdStartBanner />
        <main className="container">
          <Routes>
            <Route path="/" element={<Navigate to="/ranking" replace />} />
            <Route path="/ranking" element={<Ranking />} />
            <Route path="/reuniones" element={<Reuniones />} />
            <Route path="/reuniones/:id" element={<ReunionDetalle />} />
            <Route path="/estadisticas" element={<Estadisticas />} />
            <Route path="/login" element={<Login />} />
            <Route path="/admin" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/admin/temporada/nueva" element={<ProtectedRoute><CrearTemporada /></ProtectedRoute>} />
            <Route path="/admin/reuniones/nueva" element={<ProtectedRoute><GestionReunion modo="crear" /></ProtectedRoute>} />
            <Route path="/admin/reuniones/:id/editar" element={<ProtectedRoute><GestionReunion modo="editar" /></ProtectedRoute>} />
          </Routes>
        </main>
      </BrowserRouter>
    </AuthProvider>
  )
}
