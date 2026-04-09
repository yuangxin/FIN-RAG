import { useState } from 'react'
import DashboardPage from './pages/DashboardPage'

function App() {
  const [darkMode, setDarkMode] = useState(true)

  return (
    <div className={darkMode ? 'dark' : ''}>
      <div className={`min-h-screen ${darkMode ? 'bg-mesh text-gray-100' : 'bg-mesh-light text-gray-900'}`}>
        <DashboardPage darkMode={darkMode} setDarkMode={setDarkMode} />
      </div>
    </div>
  )
}

export default App
