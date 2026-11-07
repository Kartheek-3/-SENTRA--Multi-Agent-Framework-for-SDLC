import React, { useState } from 'react';
import { useAuth } from '../firebase/AuthContext';

export type LoginPageProps = {
  onSuccess: () => void;
  onNavigateSignup: () => void;
  onBackToLanding: () => void;
};

export function LoginPage({ onSuccess, onNavigateSignup, onBackToLanding }: LoginPageProps) {
  const { login, loginWithGoogle, demoLogin, error, clearError } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [localErr, setLocalErr] = useState('');
  const [resetSent, setResetSent] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      setLocalErr('Please enter both email and password.');
      return;
    }
    setLocalErr('');
    setLoading(true);
    try {
      await login(email, password);
      onSuccess();
    } catch (err: any) {
      setLocalErr(err.message || 'Login failed.');
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
      setLocalErr(err.message || 'Google sign-in failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleDemoAccess = async () => {
    setLoading(true);
    try {
      await demoLogin('engineer@seam.internal', 'Kartheek Mudi');
      onSuccess();
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
          <h2>Sign in to SEAM</h2>
          <p>Access your workspace, autonomous agents, and verified delivery pipelines.</p>
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
          <span>OR CONTINUE WITH EMAIL</span>
        </div>

        {/* Email Form */}
        <form onSubmit={handleSubmit} className="authForm">
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
            <div className="labelWithAction">
              <label htmlFor="auth-password">PASSWORD</label>
              <button
                type="button"
                className="forgotPassLink"
                onClick={() => setLocalErr('Password reset link will be sent to the email address.')}
              >
                Forgot password?
              </button>
            </div>
            <input
              id="auth-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••••••"
              required
              disabled={loading}
              autoComplete="current-password"
            />
          </div>

          <button type="submit" className="authSubmitBtn" disabled={loading}>
            {loading ? 'Authenticating...' : 'Sign In to Workspace →'}
          </button>
        </form>

        {/* Quick Demo Bypass for local evaluations */}
        <div className="authDemoAccess">
          <button type="button" className="demoBypassBtn" onClick={handleDemoAccess} disabled={loading}>
            ⚡ Instant Access (Demo Engineer Profile)
          </button>
        </div>

        {/* Footer switch */}
        <div className="authFooter">
          <span>Don't have an account?</span>
          <button type="button" className="switchAuthLink" onClick={onNavigateSignup}>
            Create an account
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
