import { useState, useEffect } from 'react';
import { AuthScreen } from './screens/AuthScreen';
import { SkillSelectionScreen } from './screens/SkillSelectionScreen';
import { SimulationScreen } from './screens/SimulationScreen';
import { ResultsScreen } from './screens/ResultsScreen';
import { api } from './lib/api';

export type Screen = 'auth' | 'skills' | 'simulation' | 'results';

export interface User {
  user_id: string;
  email: string;
  full_name: string;
  is_phone_verified: boolean;
}

function App() {
  const [currentScreen, setCurrentScreen] = useState<Screen>('auth');
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(localStorage.getItem('token'));
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check if user is already logged in
    const checkAuth = async () => {
      if (token) {
        try {
          api.setToken(token);
          const userData = await api.getMe();
          setUser(userData);
          setCurrentScreen('skills');
        } catch (error) {
          console.error('Auth check failed:', error);
          localStorage.removeItem('token');
          setToken(null);
        }
      }
      setIsLoading(false);
    };

    checkAuth();
  }, [token]);

  const handleLogin = (userData: User, accessToken: string) => {
    setUser(userData);
    setToken(accessToken);
    localStorage.setItem('token', accessToken);
    api.setToken(accessToken);
    setCurrentScreen('skills');
  };

  const handleLogout = () => {
    setUser(null);
    setToken(null);
    localStorage.removeItem('token');
    api.setToken(null);
    setCurrentScreen('auth');
  };

  const handleStartSimulation = () => {
    setCurrentScreen('simulation');
  };

  const handleSimulationComplete = () => {
    setCurrentScreen('results');
  };

  const handleBackToSkills = () => {
    setCurrentScreen('skills');
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0B0C10]">
        <div className="animate-spin w-8 h-8 border-2 border-[#FF6B2B] border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#0B0C10]">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 bg-[#0B0C10]/80 backdrop-blur-md border-b border-[#1E1F24]">
        <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-[#FF6B2B] to-[#F5C842] rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-sm">C</span>
            </div>
            <span className="font-semibold text-white">Crestal</span>
          </div>
          
          {user && (
            <div className="flex items-center gap-4">
              <span className="text-sm text-[#A0A2A8]">{user.full_name}</span>
              <button
                onClick={handleLogout}
                className="text-sm text-[#6B6D75] hover:text-white transition-colors"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-16">
        {currentScreen === 'auth' && (
          <AuthScreen onLogin={handleLogin} />
        )}
        
        {currentScreen === 'skills' && user && (
          <SkillSelectionScreen 
            user={user} 
            onStartSimulation={handleStartSimulation}
          />
        )}
        
        {currentScreen === 'simulation' && user && (
          <SimulationScreen 
            user={user}
            onComplete={handleSimulationComplete}
          />
        )}
        
        {currentScreen === 'results' && user && (
          <ResultsScreen 
            user={user}
            onBackToSkills={handleBackToSkills}
          />
        )}
      </main>
    </div>
  );
}

export default App;
