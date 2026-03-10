import { useState } from 'react';
import { api } from '../lib/api';
import type { User } from '../App';

interface AuthScreenProps {
  onLogin: (user: User, token: string) => void;
}

export function AuthScreen({ onLogin }: AuthScreenProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [showOTP, setShowOTP] = useState(false);
  
  // Form fields
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [phone, setPhone] = useState('');
  const [state, setState] = useState('');
  const [otp, setOtp] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      if (isLogin) {
        const response = await api.login(email, password);
        onLogin(response.user, response.access_token);
      } else {
        const response = await api.register({
          email,
          password,
          full_name: fullName,
          phone,
          state,
        });
        
        // Store token temporarily
        api.setToken(response.access_token);
        localStorage.setItem('token', response.access_token);
        
        // Show OTP verification
        setShowOTP(true);
      }
    } catch (err: any) {
      setError(err.message || 'Something went wrong');
    } finally {
      setIsLoading(false);
    }
  };

  const handleVerifyOTP = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setIsLoading(true);

    try {
      await api.verifyOTP(phone, otp);
      
      // Get user data
      const userData = await api.getMe();
      const token = localStorage.getItem('token')!;
      
      onLogin(userData, token);
    } catch (err: any) {
      setError(err.message || 'Invalid OTP');
    } finally {
      setIsLoading(false);
    }
  };

  if (showOTP) {
    return (
      <div className="screen-container flex items-center justify-center">
        <div className="w-full max-w-md animate-fade-in">
          <div className="text-center mb-8">
            <h1 className="text-2xl font-bold text-white mb-2">Verify Your Phone</h1>
            <p className="text-[#A0A2A8]">
              Enter the 6-digit code sent to {phone}
            </p>
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
              {error}
            </div>
          )}

          <form onSubmit={handleVerifyOTP} className="space-y-4">
            <div>
              <label className="block text-sm text-[#A0A2A8] mb-2">OTP Code</label>
              <input
                type="text"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                placeholder="123456"
                maxLength={6}
                className="input text-center text-2xl tracking-widest"
                required
              />
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="btn btn-primary w-full"
            >
              {isLoading ? (
                <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
              ) : (
                'Verify'
              )}
            </button>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="screen-container flex items-center justify-center">
      <div className="w-full max-w-md animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 mx-auto mb-4 bg-gradient-to-br from-[#FF6B2B] to-[#F5C842] rounded-xl flex items-center justify-center">
            <span className="text-white font-bold text-2xl">C</span>
          </div>
          <h1 className="text-2xl font-bold text-white mb-2">
            {isLogin ? 'Welcome Back' : 'Join Crestal'}
          </h1>
          <p className="text-[#A0A2A8]">
            {isLogin 
              ? 'Sign in to continue your journey' 
              : 'Prove your skills. Rise to your level.'}
          </p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-500/10 border border-red-500/30 rounded-lg text-red-400 text-sm">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {!isLogin && (
            <>
              <div>
                <label className="block text-sm text-[#A0A2A8] mb-2">Full Name</label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Chukwuemeka Obi"
                  className="input"
                  required
                />
              </div>

              <div>
                <label className="block text-sm text-[#A0A2A8] mb-2">Phone Number</label>
                <input
                  type="tel"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+2348012345678"
                  className="input"
                  required
                />
              </div>

              <div>
                <label className="block text-sm text-[#A0A2A8] mb-2">State</label>
                <select
                  value={state}
                  onChange={(e) => setState(e.target.value)}
                  className="input"
                  required
                >
                  <option value="">Select your state</option>
                  <option value="Lagos">Lagos</option>
                  <option value="Abuja">Abuja FCT</option>
                  <option value="Kano">Kano</option>
                  <option value="Rivers">Rivers</option>
                  <option value="Enugu">Enugu</option>
                  <option value="Ogun">Ogun</option>
                  <option value="Oyo">Oyo</option>
                  <option value="Delta">Delta</option>
                  <option value="Kaduna">Kaduna</option>
                  <option value="Other">Other</option>
                </select>
              </div>
            </>
          )}

          <div>
            <label className="block text-sm text-[#A0A2A8] mb-2">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="input"
              required
            />
          </div>

          <div>
            <label className="block text-sm text-[#A0A2A8] mb-2">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="input"
              minLength={8}
              required
            />
          </div>

          <button
            type="submit"
            disabled={isLoading}
            className="btn btn-primary w-full"
          >
            {isLoading ? (
              <span className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full" />
            ) : (
              isLogin ? 'Sign In' : 'Create Account'
            )}
          </button>
        </form>

        <div className="mt-6 text-center">
          <button
            onClick={() => setIsLogin(!isLogin)}
            className="text-sm text-[#FF6B2B] hover:underline"
          >
            {isLogin 
              ? "Don't have an account? Sign up" 
              : 'Already have an account? Sign in'}
          </button>
        </div>

        <div className="mt-8 text-center">
          <p className="text-xs text-[#6B6D75]">
            By joining, you agree to prove your skills through real work.
            <br />
            No CV required. Your results are your credentials.
          </p>
        </div>
      </div>
    </div>
  );
}
