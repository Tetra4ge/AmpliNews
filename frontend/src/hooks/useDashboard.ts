import { useState, useEffect, type FormEvent } from 'react';
import { supabase } from '../lib/supabase';
import { fetchUserProfile, syncUser, fetchFeed, fetchArticleById, logArticleRead, fetchOpposingView, type UserProfileResponse, type Article, type OpposingViewResponse } from '../lib/api';

type ViewState = 'loading' | 'onboarding' | 'ready' | 'error';

export function useDashboard(navigate: any) {
  const [view, setView] = useState<ViewState>('loading');
  const [profile, setProfile] = useState<UserProfileResponse | null>(null);
  const [feed, setFeed] = useState<Article[]>([]);
  
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const [leaning, setLeaning] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [debugLog, setDebugLog] = useState<string>('Starting load...');

  // Reading View State
  const [selectedArticleId, setSelectedArticleId] = useState<string | null>(null);
  const [fullArticle, setFullArticle] = useState<any | null>(null);
  const [loadingArticle, setLoadingArticle] = useState(false);
  const [readStartTime, setReadStartTime] = useState<number | null>(null);
  const [isLiked, setIsLiked] = useState<boolean>(false);
  const [isBiased, setIsBiased] = useState<boolean>(false);

  // Opposing View State
  const [opposingArticle, setOpposingArticle] = useState<OpposingViewResponse | null>(null);
  const [loadingOpposing, setLoadingOpposing] = useState(false);
  const [opposingError, setOpposingError] = useState<string | null>(null);

  // Preferences Editing State
  const [isPreferencesOpen, setIsPreferencesOpen] = useState(false);
  const [prefSubmitting, setPrefSubmitting] = useState(false);
  const [prefError, setPrefError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      setDebugLog('Checking session...');
      const { data } = await supabase.auth.getSession();
      if (!data.session) {
        navigate('/login', { replace: true });
        return;
      }

      try {
        setDebugLog('Fetching user profile...');
        const res = await fetchUserProfile();
        if (!cancelled) {
          setDebugLog('Profile fetched. Setting ready...');
          setProfile(res.data);
          setView('ready');
          
          try {
            const feedRes = await fetchFeed();
            if (!cancelled) {
              setFeed(feedRes.data.feed || []);
            }
          } catch (feedErr) {
            console.error("Could not fetch feed", feedErr);
          }
        }
      } catch (err: any) {
        if (cancelled) return;
        setDebugLog(`Error occurred: ${err.message}`);
        if (err?.response?.status === 404) {
          setView('onboarding');
        } else {
          const detail = err?.response?.data?.detail || err.message;
          setError(`API Error: ${detail}`);
          setView('error');
        }
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, [navigate]);

  function toggleTopic(topic: string) {
    setSelectedTopics((prev) =>
      prev.includes(topic) ? prev.filter((t) => t !== topic) : [...prev, topic]
    );
  }

  async function handleOnboardingSubmit(e: FormEvent) {
    e.preventDefault();
    if (selectedTopics.length === 0) return;
    setSubmitting(true);
    setError(null);

    try {
      await syncUser({ selected_topics: selectedTopics, baseline_leaning: leaning });
      const res = await fetchUserProfile();
      setProfile(res.data);
      setView('ready');
      
      const feedRes = await fetchFeed();
      setFeed(feedRes.data.feed || []);
    } catch {
      setError('Failed to save your preferences. Please try again.');
    } finally {
      setSubmitting(false);
    }
  }

  function openPreferences() {
    setSelectedTopics([]);
    setLeaning(profile?.baseline_political_leaning ?? 0);
    setPrefError(null);
    setIsPreferencesOpen(true);
  }

  function closePreferences() {
    setIsPreferencesOpen(false);
    setPrefError(null);
  }

  async function handlePreferencesSubmit(e: FormEvent) {
    e.preventDefault();
    if (selectedTopics.length === 0) return;
    setPrefSubmitting(true);
    setPrefError(null);

    try {
      await syncUser({ selected_topics: selectedTopics, baseline_leaning: leaning });
      const [profileRes, feedRes] = await Promise.all([fetchUserProfile(), fetchFeed()]);
      setProfile(profileRes.data);
      setFeed(feedRes.data.feed || []);
      setIsPreferencesOpen(false);
    } catch {
      setPrefError('Failed to update your preferences. Please try again.');
    } finally {
      setPrefSubmitting(false);
    }
  }

  async function handleSignOut() {
    await supabase.auth.signOut();
    navigate('/login', { replace: true });
  }

  async function handleArticleClick(id: string) {
    setSelectedArticleId(id);
    setReadStartTime(Date.now());
    setIsLiked(false);
    setIsBiased(false);
    setOpposingArticle(null);
    setOpposingError(null);
    setLoadingArticle(true);
    setFullArticle(null);
    try {
      const res = await fetchArticleById(id);
      setFullArticle(res.data);
    } catch (err) {
      console.error("Failed to fetch full article", err);
    } finally {
      setLoadingArticle(false);
    }
  }

  async function closeReadingView() {
    if (selectedArticleId && readStartTime) {
      const duration = Math.max(0, Math.round((Date.now() - readStartTime) / 1000));
      try {
        await logArticleRead({
          article_id: selectedArticleId,
          read_duration_seconds: duration,
          liked: isLiked,
          rejected_biased: isBiased
        });
      } catch (err) {
        console.error("Failed to log reading interaction", err);
      }
    }
    setSelectedArticleId(null);
    setFullArticle(null);
    setReadStartTime(null);
    setIsLiked(false);
    setIsBiased(false);
    setOpposingArticle(null);
    setOpposingError(null);
  }

  async function handleLikeClick() {
    if (!selectedArticleId) return;
    const newLiked = !isLiked;
    setIsLiked(newLiked);
    if (newLiked) setIsBiased(false);

    const duration = readStartTime ? Math.max(0, Math.round((Date.now() - readStartTime) / 1000)) : 0;
    try {
      await logArticleRead({
        article_id: selectedArticleId,
        read_duration_seconds: duration,
        liked: newLiked,
        rejected_biased: false
      });
    } catch (err) {
      console.error("Failed to log like interaction", err);
    }
  }

  async function handleBiasedClick() {
    if (!selectedArticleId) return;
    const newBiased = !isBiased;
    setIsBiased(newBiased);
    if (newBiased) setIsLiked(false);

    const duration = readStartTime ? Math.max(0, Math.round((Date.now() - readStartTime) / 1000)) : 0;
    try {
      await logArticleRead({
        article_id: selectedArticleId,
        read_duration_seconds: duration,
        liked: false,
        rejected_biased: newBiased
      });
    } catch (err) {
      console.error("Failed to log biased interaction", err);
    }
  }

  async function handleOtherSideClick() {
    if (!selectedArticleId) return;
    setLoadingOpposing(true);
    setOpposingError(null);
    setOpposingArticle(null);
    try {
      const res = await fetchOpposingView(selectedArticleId);
      setOpposingArticle(res.data);
    } catch (err: any) {
      if (err.response?.status === 404) {
        setOpposingError("No opposing viewpoints found for this specific story yet.");
      } else {
        setOpposingError("Failed to fetch opposing view.");
      }
    } finally {
      setLoadingOpposing(false);
    }
  }

  return {
    view,
    profile,
    feed,
    selectedTopics,
    leaning,
    submitting,
    error,
    debugLog,
    selectedArticleId,
    fullArticle,
    loadingArticle,
    isLiked,
    isBiased,
    opposingArticle,
    loadingOpposing,
    opposingError,
    isPreferencesOpen,
    prefSubmitting,
    prefError,
    setLeaning,
    toggleTopic,
    handleOnboardingSubmit,
    handleSignOut,
    handleArticleClick,
    closeReadingView,
    handleLikeClick,
    handleBiasedClick,
    handleOtherSideClick,
    openPreferences,
    closePreferences,
    handlePreferencesSubmit
  };
}
