import { Navigate, Route, Routes } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import AppShell from './components/layout/AppShell.jsx';
import Login from './pages/Login.jsx';
import Register from './pages/Register.jsx';
import Dashboard from './pages/Dashboard.jsx';
import History from './pages/History.jsx';
import NewInterview from './pages/NewInterview.jsx';
import InterviewRoom from './pages/InterviewRoom.jsx';
import SessionDetail from './pages/SessionDetail.jsx';
import { useAuth } from './store/auth.js';

function Protected({ children }) {
  const token = useAuth((s) => s.token);
  return token ? children : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <AnimatePresence mode="wait">
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route
          element={
            <Protected>
              <AppShell />
            </Protected>
          }
        >
          <Route path="/" element={<Dashboard />} />
          <Route path="/history" element={<History />} />
          <Route path="/new" element={<NewInterview />} />
          <Route path="/interviews/:id" element={<InterviewRoom />} />
          <Route path="/sessions/:id" element={<SessionDetail />} />
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </AnimatePresence>
  );
}
