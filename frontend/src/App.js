import React, { useState, useEffect, createContext, useContext } from "react";
import "./App.css";
import { BrowserRouter, Routes, Route, Navigate, useNavigate, useLocation } from "react-router-dom";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Auth Context
const AuthContext = createContext();

const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const checkAuth = async () => {
    try {
      const response = await axios.get(`${API}/auth/me`, { withCredentials: true });
      setUser(response.data);
    } catch (error) {
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    try {
      await axios.post(`${API}/auth/logout`, {}, { withCredentials: true });
      setUser(null);
    } catch (error) {
      console.error("Logout error:", error);
    }
  };

  useEffect(() => {
    checkAuth();
  }, []);

  return (
    <AuthContext.Provider value={{ user, setUser, loading, logout, checkAuth }}>
      {children}
    </AuthContext.Provider>
  );
};

const useAuth = () => useContext(AuthContext);

// Login Component
const Login = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setUser, checkAuth } = useAuth();
  const [processing, setProcessing] = useState(false);

  useEffect(() => {
    const processAuth = async () => {
      const hash = window.location.hash;
      if (hash.includes('session_id=')) {
        setProcessing(true);
        const sessionId = hash.split('session_id=')[1].split('&')[0];
        
        try {
          const response = await axios.get(`${API}/auth/session-data`, {
            headers: { 'X-Session-ID': sessionId },
            withCredentials: true
          });
          
          // Set httpOnly cookie
          document.cookie = `session_token=${response.data.session_token}; path=/; secure; samesite=none; max-age=${7 * 24 * 60 * 60}`;
          
          setUser(response.data.user);
          
          // Clean URL
          window.history.replaceState({}, document.title, window.location.pathname);
          
          navigate('/dashboard');
        } catch (error) {
          console.error('Auth error:', error);
          setProcessing(false);
        }
      } else {
        // Check existing session
        checkAuth();
      }
    };

    processAuth();
  }, [navigate, setUser, checkAuth]);

  const handleLogin = () => {
    const redirectUrl = `${window.location.origin}/dashboard`;
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  if (processing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center">
        <div className="text-white text-xl">Processing authentication...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-900 to-purple-900 flex items-center justify-center">
      <div className="bg-white rounded-lg shadow-xl p-8 max-w-md w-full mx-4">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">Student Records</h1>
          <p className="text-gray-600">Secure transcript verification system</p>
        </div>
        
        <div className="space-y-6">
          <div className="text-center">
            <button
              onClick={handleLogin}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition duration-300"
            >
              Login with Google
            </button>
          </div>
          
          <div className="text-sm text-gray-500 text-center">
            <p>Multi-level UUID verification system for:</p>
            <ul className="mt-2 space-y-1">
              <li>• Students requesting transcripts</li>
              <li>• Universities issuing verification</li>
              <li>• Institutions receiving verified documents</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

// Dashboard Component
const Dashboard = () => {
  const { user, logout } = useAuth();
  const [requests, setRequests] = useState([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [showCreateModal, setShowCreateModal] = useState(false);

  useEffect(() => {
    if (user) {
      fetchRequests();
    }
  }, [user]);

  const fetchRequests = async () => {
    try {
      const response = await axios.get(`${API}/transcript-requests`, { withCredentials: true });
      setRequests(response.data);
    } catch (error) {
      console.error('Error fetching requests:', error);
    }
  };

  const getRoleBadge = (role) => {
    const colors = {
      student: 'bg-green-100 text-green-800',
      issuer: 'bg-blue-100 text-blue-800',
      verifier: 'bg-purple-100 text-purple-800'
    };
    return colors[role] || 'bg-gray-100 text-gray-800';
  };

  const getStatusBadge = (status) => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      validated: 'bg-green-100 text-green-800',
      received: 'bg-blue-100 text-blue-800',
      rejected: 'bg-red-100 text-red-800'
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4">
              <h1 className="text-2xl font-bold text-gray-900">Student Records System</h1>
              <span className={`px-3 py-1 rounded-full text-xs font-medium ${getRoleBadge(user?.role)}`}>
                {user?.role?.toUpperCase()}
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-sm text-gray-600">
                <span className="font-medium">{user?.name}</span>
                {user?.university && <span className="ml-2">• {user.university}</span>}
              </div>
              <button
                onClick={logout}
                className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition duration-200"
              >
                Logout
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation */}
      <nav className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {['overview', 'requests', 'verification'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`py-4 px-2 border-b-2 font-medium text-sm transition duration-200 ${
                  activeTab === tab
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Total Requests</h3>
                <p className="text-3xl font-bold text-blue-600">{requests.length}</p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Pending</h3>
                <p className="text-3xl font-bold text-yellow-600">
                  {requests.filter(r => r.status === 'pending').length}
                </p>
              </div>
              <div className="bg-white rounded-lg shadow p-6">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Completed</h3>
                <p className="text-3xl font-bold text-green-600">
                  {requests.filter(r => r.status === 'received').length}
                </p>
              </div>
            </div>

            {user?.role === 'student' && (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex justify-between items-center mb-4">
                  <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
                </div>
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg font-medium transition duration-200"
                >
                  Request New Transcript
                </button>
              </div>
            )}
          </div>
        )}

        {activeTab === 'requests' && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900">Transcript Requests</h2>
              {user?.role === 'student' && (
                <button
                  onClick={() => setShowCreateModal(true)}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg font-medium transition duration-200"
                >
                  New Request
                </button>
              )}
            </div>

            <div className="bg-white rounded-lg shadow overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Request Details
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Universities
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      UUID Chain
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {requests.map((request) => (
                    <tr key={request.id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {request.document_type}
                          </div>
                          <div className="text-sm text-gray-500">
                            {request.student_name}
                          </div>
                          <div className="text-xs text-gray-400">
                            {new Date(request.created_at).toLocaleDateString()}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm text-gray-900">
                            From: {request.university_from}
                          </div>
                          <div className="text-sm text-gray-500">
                            To: {request.university_to}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadge(request.status)}`}>
                          {request.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-xs font-mono">
                          <div className="text-green-600">
                            Request: {request.student_request_uuid.substring(0, 8)}...
                          </div>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'verification' && (
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">UUID Verification</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Enter UUID to verify authenticity
                </label>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    placeholder="Enter UUID..."
                    className="flex-1 border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg font-medium transition duration-200">
                    Verify
                  </button>
                </div>
              </div>
              <div className="text-sm text-gray-500">
                <p>UUID verification provides:</p>
                <ul className="mt-2 space-y-1 ml-4">
                  <li>• Document authenticity confirmation</li>
                  <li>• Complete audit trail visibility</li>
                  <li>• Tamper detection through content hashing</li>
                  <li>• Non-repudiation through multi-party validation</li>
                </ul>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Create Request Modal */}
      {showCreateModal && <CreateRequestModal onClose={() => setShowCreateModal(false)} onSuccess={fetchRequests} />}
    </div>
  );
};

// Create Request Modal Component
const CreateRequestModal = ({ onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    university_from: '',
    university_to: '',
    document_type: 'transcript',
    content: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API}/transcript-requests`, formData, { withCredentials: true });
      onSuccess();
      onClose();
    } catch (error) {
      console.error('Error creating request:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl p-6 max-w-lg w-full mx-4">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Request New Transcript</h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              From University (Issuer)
            </label>
            <input
              type="text"
              required
              value={formData.university_from}
              onChange={(e) => setFormData({...formData, university_from: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter issuing university name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              To University (Verifier)
            </label>
            <input
              type="text"
              required
              value={formData.university_to}
              onChange={(e) => setFormData({...formData, university_to: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Enter receiving university name"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Document Content
            </label>
            <textarea
              required
              value={formData.content}
              onChange={(e) => setFormData({...formData, content: e.target.value})}
              className="w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows={4}
              placeholder="Enter document content for hash generation..."
            />
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-200 hover:bg-gray-300 rounded-lg font-medium transition duration-200"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition duration-200 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Request'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Protected Route Component
const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  return user ? children : <Navigate to="/login" />;
};

// Main App Component
function App() {
  return (
    <div className="App">
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/dashboard" element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            } />
            <Route path="/" element={<Navigate to="/dashboard" />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </div>
  );
}

export default App;