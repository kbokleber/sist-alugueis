import { BrowserRouter } from 'react-router-dom'
import AppRouter from './router/AppRouter'
import { useAuthStore } from './stores/authStore'
import ToastContainer from './components/ui/Toast'

function App() {
  return (
    <>
      <BrowserRouter>
        <AppRouter />
      </BrowserRouter>
      <ToastContainer />
    </>
  )
}

export default App
