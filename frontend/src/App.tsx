import { BrowserRouter } from 'react-router-dom'
import { useEffect } from 'react'
import AppRouter from './router/AppRouter'
import { useAuthStore } from './stores/authStore'
import ToastContainer from './components/ui/Toast'
import { authApi } from './api/auth'

function App() {
  const { token, user, hydrated, logout, setUser } = useAuthStore()

  useEffect(() => {
    if (!hydrated || !token || user) return

    authApi.me()
      .then((currentUser) => {
        setUser(currentUser)
      })
      .catch(() => {
        logout()
      })
  }, [hydrated, token, user, setUser, logout])

  if (!hydrated) {
    return null
  }

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
