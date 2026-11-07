import React, { useState } from 'react';
import { useAuth } from '../firebase/AuthContext';

export type SignupPageProps = {
  onSuccess: () => void;
  onNavigateLogin: () => void;
  onBackToLanding: () => void;
};

export function SignupPage({ onSuccess, onNavigateLogin, onBackToLanding }: SignupPageProps) {
  const { signup, loginWithGoogle, error, clearError } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [localErr, setLocalErr] = useState('');

  // Password strength calculation
  const getPasswordStrength = (pass: string) => {
    if (!pass) return { score: 0, label: 'None', color: '#6e7681' };
    let score = 0;
    if (pass.length >= 8) score += 1;
    if (/[A-Z]/.test(pass)) score += 1;
    if (/[0-9]/.test(pass)) score += 1;
    if (/[^A-Za-z0-9]/.test(pass)) score += 1;

    if (score <= 1) return { score: 1, label: 'Weak', color: '#f85149' };
    if (score === 2 || score === 3) return { score: 2, label: 'Good', color: '#cca700' };
    return { score: 3, label: 'Strong', color: '#73c991' };
  };

  const strength = getPasswordStrength(password);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setLocalErr('Please complete all required fields.');
      return;
    }
    if (password !== confirmPassword) {
      setLocalErr('Passwords do not match.');
      return;
    }
    if (password.length < 6) {
      setLocalErr('Password must be at least 6 characters long.');
      return;
    }

    setLocalErr('');
    setLoading(true);
    try {
      await signup(name, email, password);
      onSuccess();
    } catch (err: any) {
      setLocalErr(err.message || 'Signup failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = async () => {
    setLocalErr('');
    setLoading(true);
    try {
      await loginWithGoogle();
      onSuccess();
    } catch (err: any) {
      setLocalErr(err.message || 'Google sign-up failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="seamAuthContainer">
      <div className="seamAuthBackground">
        <div className="authGridOverlay" />
        <div className="authGlowSpot" />
      </div>

      <div className="seamAuthCard">
        {/* Header */}
        <div className="seamAuthHeader">
          <div className="seamAuthBrand" onClick={onBackToLanding} title="Back to SEAM Landing Page">
            <span className="authLogoIcon">⚡</span>
            <span className="authLogoText">SEAM</span>
          </div>
          <span className="authEyebrow">AUTONOMOUS ENGINEERING PLATFORM</span>
          <h2>Create your SEAM account</h2>
          <p>Join the autonomous software-engineering workspace and start generating verified software.</p>
        </div>

        {/* Error banner */}
        {(localErr || error) && (
          <div className="authErrorBanner">
            <span>⚠</span>
            <p>{localErr || error}</p>
            <button onClick={() => { setLocalErr(''); clearError(); }}>×</button>
          </div>
        )}

        {/* Google Sign In */}
        <button
          type="button"
          className="googleAuthBtn"
          onClick={handleGoogle}
          disabled={loading}
        >
          <svg width="18" height="18" viewBox="0 0 24 24">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
          </svg>
          <span>Continue with Google</span>
        </button>

        <div className="authDivider">
          <span>OR REGISTER WITH WORK EMAIL</span>
        </div>

        {/* Signup Form */}
        <form onSubmit={handleSubmit} className="authForm">
          <div className="formGroup">
            <label htmlFor="auth-name">FULL NAME</label>
            <input
              id="auth-name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Kartheek Mudi"
              disabled={loading}
              autoComplete="name"
            />
          </div>

          <div className="formGroup">
            <label htmlFor="auth-email">WORK EMAIL</label>
            <input
              id="auth-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="developer@company.com"
              required
              disabled={loading}
              autoComplete="email"
            />
          </div>

          <div className="formGroup">
            <label htmlFor="auth-password">PASSWORD</label>
            <input
              id="auth-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Minimum 6 characters"
              required
              disabled={loading}
              autoComplete="new-password"
            />
            {password && (
              <div className="passwordStrengthRow">
                <div className="strengthBarContainer">
                  <div
                    className="strengthBarFill"
                    style={{
                      width: `${(strength.score / 3) * 100}%`,
                      backgroundColor: strength.color,
                    }}
                  />
                </div>
                <span className="strengthLabel" style={{ color: strength.color }}>
                  {strength.label}
                </span>
              </div>
            )}
          </div>

          <div className="formGroup">
            <label htmlFor="auth-confirm">CONFIRM PASSWORD</label>
            <input
              id="auth-confirm"
              type="password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              placeholder="Confirm password"
              required
              disabled={loading}
              autoComplete="new-password"
            />
          </div>

          <button type="submit" className="authSubmitBtn" disabled={loading}>
            {loading ? 'Creating Account...' : 'Create Account & Launch Workspace →'}
          </button>
        </form>

        <div className="authFooter">
          <span>Already have an account?</span>
          <button type="button" className="switchAuthLink" onClick={onNavigateLogin}>
            Sign in
          </button>
        </div>

        <div className="authBackLanding">
          <button type="button" onClick={onBackToLanding}>
            ← Back to Public Website
          </button>
        </div>
      </div>
    </div>
  );
}
