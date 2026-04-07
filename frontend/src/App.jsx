import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import Nav from './components/Nav'
import Ranking from './pages/Ranking'
import Reuniones from './pages/Reuniones'
import ReunionDetalle from './pages/ReunionDetalle'
import Estadisticas from './pages/Estadisticas'

export default function App() {
  return (
    <BrowserRouter>
      <Nav />
      <main className="container">
        <Routes>
          <Route path="/" element={<Navigate to="/ranking" replace />} />
          <Route path="/ranking" element={<Ranking />} />
          <Route path="/reuniones" element={<Reuniones />} />
          <Route path="/reuniones/:id" element={<ReunionDetalle />} />
          <Route path="/estadisticas" element={<Estadisticas />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
