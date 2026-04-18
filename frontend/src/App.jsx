import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Home      from './pages/Home'
import Callback  from './pages/Callback'
import Generator from './pages/Generator'
import './index.css'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/"         element={<Home />} />
        <Route path="/callback" element={<Callback />} />
        <Route path="/generate" element={<Generator />} />
      </Routes>
    </BrowserRouter>
  )
}
