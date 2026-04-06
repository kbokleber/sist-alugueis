import { BrowserRouter } from 'react-router-dom'
import AppRouter from './router/AppRouter'
import { useAuthStore } from './stores/authStore'

function App() {
  return (
    <BrowserRouter>
      <AppRouter />
    </BrowserRouter>
  )
}

export default App
