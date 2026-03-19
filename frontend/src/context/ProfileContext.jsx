import { createContext, useContext, useState, useCallback, useEffect } from 'react';
import { getProfiles } from '../api/client.js';

const ProfileContext = createContext(null);

export function ProfileProvider({ children }) {
  const [profiles, setProfiles] = useState([]);
  const [masterProfile, setMasterProfile] = useState(null);
  const [profile, setProfileState] = useState(null);
  const [profilesError, setProfilesError] = useState(null);
  const [accountLoaded, setAccountLoaded] = useState(false);
  const [costsLoaded, setCostsLoaded] = useState(false);

  const setProfile = useCallback((next) => {
    setProfileState(next);
    setAccountLoaded(false);
    setCostsLoaded(false);
  }, []);

  const markAccountLoaded = useCallback(
    (forProfile) => {
      setAccountLoaded((prev) => (forProfile === profile ? true : prev));
    },
    [profile],
  );
  const markCostsLoaded = useCallback(
    (forProfile) => {
      setCostsLoaded((prev) => (forProfile === profile ? true : prev));
    },
    [profile],
  );

  useEffect(() => {
    let cancelled = false;
    getProfiles()
      .then(({ profiles: nextProfiles, masterProfile: nextMasterProfile }) => {
        if (!cancelled) {
          setProfiles(nextProfiles || []);
          setMasterProfile(nextMasterProfile || null);
          if (nextProfiles?.length) setProfileState((p) => (p ?? nextProfiles[0]));
        }
      })
      .catch((e) => {
        if (!cancelled) setProfilesError(e.message);
      });
    return () => { cancelled = true; };
  }, []);

  const profileDataRefreshing = Boolean(profile && (!accountLoaded || !costsLoaded));

  return (
    <ProfileContext.Provider
      value={{
        profiles,
        masterProfile,
        profile,
        setProfile,
        profilesError,
        profileDataRefreshing,
        markAccountLoaded,
        markCostsLoaded,
      }}
    >
      {children}
    </ProfileContext.Provider>
  );
}

export function useProfile() {
  const ctx = useContext(ProfileContext);
  if (!ctx) throw new Error('useProfile must be used within ProfileProvider');
  return ctx;
}
