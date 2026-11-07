import React from 'react';
import { useAuth } from '../firebase/AuthContext';

export type AccountProfileModalProps = {
  isOpen: boolean;
  onClose: () => void;
  onOpenSettings: () => void;
  projectCount: number;
};

export function AccountProfileModal({
  isOpen,
  onClose,
  onOpenSettings,
  projectCount,
}: AccountProfileModalProps) {
  const { currentUser, userProfile, logout } = useAuth();

  if (!isOpen) return null;

  const displayName = userProfile?.displayName || currentUser?.displayName || currentUser?.email?.split('@')[0] || 'SEAM Engineer';
  const email = userProfile?.email || currentUser?.email || 'engineer@seam.internal';
  const provider = userProfile?.provider || currentUser?.providerData?.[0]?.providerId || 'Email/Password';
  const initial = displayName.charAt(0).toUpperCase();

  const handleSignOut = async () => {
    await logout();
    onClose();
  };

  return (
    <div className="accountModalBackdrop" onClick={onClose}>
      <div className="accountModalCard" onClick={e => e.stopPropagation()}>
        <div className="accountModalHeader">
          <div className="accountModalAvatar">
            {userProfile?.photoURL ? (
              <img src={userProfile.photoURL} alt={displayName} />
            ) : (
              <span>{initial}</span>
            )}
          </div>
          <div className="accountModalInfo">
            <h4>{displayName}</h4>
            <span className="accountEmail">{email}</span>
            <span className="accountProviderBadge">{provider.replace('.com', '')}</span>
          </div>
          <button className="accountModalCloseBtn" onClick={onClose}>×</button>
        </div>

        <div className="accountModalStats">
          <div className="statItem">
            <span>PROJECTS</span>
            <strong>{projectCount}</strong>
          </div>
          <div className="statItem">
            <span>PERMISSIONS</span>
            <strong className="badgeGood">FULL ACCESS</strong>
          </div>
          <div className="statItem">
            <span>PERSISTENCE</span>
            <strong>FIRESTORE</strong>
          </div>
        </div>

        <div className="accountModalDetails">
          <div className="detailRow">
            <span>User UID</span>
            <code>{currentUser?.uid || 'seam-user-local'}</code>
          </div>
          <div className="detailRow">
            <span>Environment</span>
            <span>Production Engineering Workspace</span>
          </div>
          <div className="detailRow">
            <span>Role</span>
            <span>Lead Autonomous Software Engineer</span>
          </div>
        </div>

        <div className="accountModalActions">
          <button
            className="accountSettingsBtn"
            onClick={() => {
              onClose();
              onOpenSettings();
            }}
          >
            ⚙ Settings & Preferences
          </button>
          <button className="accountSignOutBtn" onClick={handleSignOut}>
            Sign Out
          </button>
        </div>
      </div>
    </div>
  );
}
