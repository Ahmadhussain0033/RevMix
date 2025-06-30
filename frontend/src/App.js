import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import { supabase } from './lib/supabase';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

// Component: Authentication Screen
function AuthScreen({ onLogin }) {
  const [currentTab, setCurrentTab] = useState('login');
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.username.trim() || !formData.password.trim()) {
      setError('Please fill in all required fields');
      return;
    }
    
    setIsLoading(true);
    setError('');
    
    try {
      const endpoint = currentTab === 'login' ? '/api/auth/login' : '/api/auth/register';
      const payload = currentTab === 'login' 
        ? { username: formData.username, password: formData.password }
        : { username: formData.username, email: formData.email, password: formData.password };

      const response = await fetch(`${BACKEND_URL}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      
      const data = await response.json();
      
      if (response.ok) {
        // Store session data
        localStorage.setItem('revmix_session', JSON.stringify(data.session));
        onLogin(data.user, data.session);
      } else {
        setError(data.detail || 'Authentication failed');
      }
    } catch (error) {
      console.error('Auth error:', error);
      setError('Network error. Please try again.');
    }
    setIsLoading(false);
  };

  return (
    <div className="auth-screen">
      <div className="auth-container">
        <div className="logo-section">
          <h1 className="app-title">🎤 RevMix</h1>
          <p className="app-subtitle">Where Bars Battle & Beats Drop</p>
        </div>
        
        <div className="auth-tabs">
          <button 
            className={`auth-tab ${currentTab === 'login' ? 'active' : ''}`}
            onClick={() => setCurrentTab('login')}
          >
            Login
          </button>
          <button 
            className={`auth-tab ${currentTab === 'register' ? 'active' : ''}`}
            onClick={() => setCurrentTab('register')}
          >
            Register
          </button>
        </div>
        
        <form onSubmit={handleSubmit} className="auth-form">
          <h2>{currentTab === 'login' ? 'Welcome Back' : 'Join the Cypher'}</h2>
          
          {error && (
            <div style={{ color: '#ff4444', marginBottom: '1rem', textAlign: 'center' }}>
              {error}
            </div>
          )}
          
          <div className="form-group">
            <label htmlFor="username">Username</label>
            <input
              type="text"
              id="username"
              name="username"
              value={formData.username}
              onChange={handleInputChange}
              placeholder="Enter your MC name"
              className="form-input"
              required
            />
          </div>

          {currentTab === 'register' && (
            <div className="form-group">
              <label htmlFor="email">Email</label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="Enter your email"
                className="form-input"
                required
              />
            </div>
          )}
          
          <div className="form-group">
            <label htmlFor="password">Password</label>
            <input
              type="password"
              id="password"
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              placeholder="Enter your password"
              className="form-input"
              required
            />
          </div>
          
          <button 
            type="submit"
            disabled={isLoading}
            className="auth-btn"
          >
            {isLoading ? 'Loading...' : 
             currentTab === 'login' ? 'Start Spitting 🔥' : 'Join the Battle 🚀'}
          </button>
        </form>
        
        <div className="features-preview">
          <div className="feature-item">
            <span className="feature-icon">🎵</span>
            <span>Live Audio Battles</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">⚔️</span>
            <span>Real-time Judging</span>
          </div>
          <div className="feature-item">
            <span className="feature-icon">🏆</span>
            <span>Earn XP & Badges</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// Component: Audio Timeline with Drag & Drop
function AudioTimeline({ onTimelineReady }) {
  const [audioClips, setAudioClips] = useState([]);
  const [timelineClips, setTimelineClips] = useState([]);
  const [availableEffects, setAvailableEffects] = useState([]);
  const [draggedClip, setDraggedClip] = useState(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [playbackProgress, setPlaybackProgress] = useState(0);
  const [totalDuration, setTotalDuration] = useState(0);

  const fileInputRef = useRef(null);
  const playbackRef = useRef(null);

  useEffect(() => {
    fetchAudioEffects();
  }, []);

  const fetchAudioEffects = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/audio-effects`);
      const data = await response.json();
      setAvailableEffects(data.effects || []);
    } catch (error) {
      console.error('Error fetching audio effects:', error);
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith('audio/')) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const audioData = e.target.result.split(',')[1]; // Remove data:audio/xxx;base64,
        const newClip = {
          id: Date.now(),
          name: file.name.replace(/\.[^/.]+$/, ""),
          audio_data: audioData,
          duration: 10, // Default duration, would be calculated in real implementation
          type: 'custom',
          file: file
        };
        setAudioClips(prev => [...prev, newClip]);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleDragStart = (clip) => {
    setDraggedClip(clip);
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (draggedClip) {
      const newTimelineClip = {
        ...draggedClip,
        timelineId: Date.now(),
        position: timelineClips.length * 2 // Simple positioning
      };
      setTimelineClips(prev => [...prev, newTimelineClip]);
      setDraggedClip(null);
      calculateTotalDuration([...timelineClips, newTimelineClip]);
    }
  };

  const removeClipFromTimeline = (timelineId) => {
    const updatedClips = timelineClips.filter(clip => clip.timelineId !== timelineId);
    setTimelineClips(updatedClips);
    calculateTotalDuration(updatedClips);
  };

  const calculateTotalDuration = (clips) => {
    const duration = clips.reduce((total, clip) => total + clip.duration, 0);
    setTotalDuration(duration);
  };

  const playTimeline = () => {
    if (timelineClips.length === 0) return;
    
    setIsPlaying(true);
    setPlaybackProgress(0);
    
    // Simulate playback progress
    const interval = setInterval(() => {
      setPlaybackProgress(prev => {
        if (prev >= totalDuration) {
          setIsPlaying(false);
          clearInterval(interval);
          return 0;
        }
        return prev + 0.1;
      });
    }, 100);
    
    playbackRef.current = interval;
  };

  const stopPlayback = () => {
    setIsPlaying(false);
    setPlaybackProgress(0);
    if (playbackRef.current) {
      clearInterval(playbackRef.current);
    }
  };

  const generateFinalAudio = () => {
    if (timelineClips.length === 0) {
      alert('Please add audio clips to the timeline first');
      return;
    }

    // In a real implementation, this would merge the audio clips
    const finalAudioData = {
      audio_timeline: timelineClips.map(clip => ({
        name: clip.name,
        audio_data: clip.audio_data,
        position: clip.position,
        duration: clip.duration
      })),
      total_duration: totalDuration
    };

    onTimelineReady(finalAudioData);
  };

  return (
    <div className="audio-timeline-container">
      <div className="timeline-header">
        <h3>🎵 Audio Timeline Studio</h3>
        <div className="timeline-controls">
          <button 
            className="timeline-btn"
            onClick={() => fileInputRef.current?.click()}
          >
            📁 Upload Audio
          </button>
          <button 
            className="timeline-btn"
            onClick={generateFinalAudio}
            disabled={timelineClips.length === 0}
          >
            🚀 Generate Track
          </button>
        </div>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="audio/*"
        onChange={handleFileUpload}
        style={{ display: 'none' }}
      />

      <div className="audio-clips-library">
        <h4>📚 Audio Library</h4>
        <div className="clips-grid">
          {/* Built-in Effects */}
          {availableEffects.map(effect => (
            <div
              key={effect.id}
              className="audio-clip-item"
              draggable
              onDragStart={() => handleDragStart(effect)}
            >
              <div className="clip-name">{effect.name}</div>
              <div className="clip-duration">{effect.duration}s</div>
              <div style={{ fontSize: '0.8rem', color: '#888' }}>Built-in</div>
            </div>
          ))}
          
          {/* Custom Uploads */}
          {audioClips.map(clip => (
            <div
              key={clip.id}
              className="audio-clip-item"
              draggable
              onDragStart={() => handleDragStart(clip)}
            >
              <div className="clip-name">{clip.name}</div>
              <div className="clip-duration">{clip.duration}s</div>
              <div style={{ fontSize: '0.8rem', color: '#888' }}>Custom</div>
            </div>
          ))}
        </div>
      </div>

      <div className="timeline-section">
        <h4>🎬 Timeline Track</h4>
        <div className="timeline-ruler">
          <div className="ruler-marks">
            {Array.from({ length: Math.ceil(totalDuration / 5) + 1 }, (_, i) => (
              <div key={i} className="ruler-mark">
                <div className="ruler-label">{i * 5}s</div>
              </div>
            ))}
          </div>
        </div>
        
        <div 
          className={`timeline-track ${draggedClip ? 'drag-over' : ''}`}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
        >
          {timelineClips.length === 0 ? (
            <div style={{ 
              textAlign: 'center', 
              padding: '2rem', 
              color: '#666',
              fontSize: '1.1rem'
            }}>
              🎵 Drag audio clips here to build your track
            </div>
          ) : (
            <div className="timeline-clips">
              {timelineClips.map(clip => (
                <div key={clip.timelineId} className="timeline-clip">
                  <span>{clip.name}</span>
                  <button
                    className="remove-clip"
                    onClick={() => removeClipFromTimeline(clip.timelineId)}
                  >
                    ×
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="timeline-playback">
        <button 
          className="playback-btn"
          onClick={isPlaying ? stopPlayback : playTimeline}
          disabled={timelineClips.length === 0}
        >
          {isPlaying ? '⏹️ Stop' : '▶️ Play Timeline'}
        </button>
        
        <div className="playback-progress">
          <div 
            className="progress-fill"
            style={{ 
              width: totalDuration > 0 ? `${(playbackProgress / totalDuration) * 100}%` : '0%' 
            }}
          />
        </div>
        
        <span style={{ color: '#00ffff', fontWeight: '600' }}>
          {Math.floor(playbackProgress)}s / {Math.floor(totalDuration)}s
        </span>
      </div>
    </div>
  );
}

// Component: Enhanced Audio Recorder with Timeline Integration
function AudioRecorder({ onAudioReady, maxDuration = 120 }) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordedAudio, setRecordedAudio] = useState(null);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioFile, setAudioFile] = useState(null);
  const [uploadMode, setUploadMode] = useState('record');
  const [showTimeline, setShowTimeline] = useState(false);
  const [timelineData, setTimelineData] = useState(null);
  
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);
  const fileInputRef = useRef(null);

  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 44100
        } 
      });

      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      audioChunksRef.current = [];
      setRecordingTime(0);

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { 
          type: 'audio/webm' 
        });
        const audioUrl = URL.createObjectURL(audioBlob);
        setRecordedAudio({ url: audioUrl, blob: audioBlob });
        
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorderRef.current.start(1000);
      setIsRecording(true);

      timerRef.current = setInterval(() => {
        setRecordingTime(prev => {
          const newTime = prev + 1;
          if (newTime >= maxDuration) {
            stopRecording();
            return maxDuration;
          }
          return newTime;
        });
      }, 1000);

    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Microphone access required. Please check your browser permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      if (!file.type.startsWith('audio/')) {
        alert('Please select an audio file');
        return;
      }

      if (file.size > 10 * 1024 * 1024) {
        alert('File size must be less than 10MB');
        return;
      }

      const audioUrl = URL.createObjectURL(file);
      setAudioFile({ url: audioUrl, file: file });
    }
  };

  const convertToBase64 = (audioSource) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const base64String = reader.result.split(',')[1];
        resolve(base64String);
      };
      reader.onerror = reject;
      
      if (audioSource.blob) {
        reader.readAsDataURL(audioSource.blob);
      } else if (audioSource.file) {
        reader.readAsDataURL(audioSource.file);
      }
    });
  };

  const handleTimelineReady = (timelineData) => {
    setTimelineData(timelineData);
    setShowTimeline(false);
    alert('🎵 Timeline track generated! You can now submit your performance.');
  };

  const handleSubmit = async () => {
    let audioSource = null;
    let finalAudioData = null;

    // Check if we have timeline data (multi-track audio)
    if (timelineData) {
      finalAudioData = {
        audio_data: 'timeline_placeholder', // In real implementation, would merge audio clips
        duration: timelineData.total_duration,
        source: 'timeline',
        audio_timeline: timelineData.audio_timeline
      };
    } else {
      // Single audio recording/upload
      if (uploadMode === 'record' && recordedAudio) {
        audioSource = recordedAudio;
      } else if (uploadMode === 'upload' && audioFile) {
        audioSource = audioFile;
      }
      
      if (!audioSource) {
        alert('Please record, upload, or create a timeline track first');
        return;
      }

      try {
        const base64Audio = await convertToBase64(audioSource);
        finalAudioData = {
          audio_data: base64Audio,
          duration: uploadMode === 'record' ? recordingTime : 60,
          source: uploadMode,
          audio_timeline: []
        };
      } catch (error) {
        console.error('Error processing audio:', error);
        alert('Error processing audio file');
        return;
      }
    }

    onAudioReady(finalAudioData);
  };

  const clearAudio = () => {
    setRecordedAudio(null);
    setAudioFile(null);
    setTimelineData(null);
    setRecordingTime(0);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="audio-recorder">
      <div className="recorder-tabs">
        <button 
          className={`tab-btn ${uploadMode === 'record' ? 'active' : ''}`}
          onClick={() => setUploadMode('record')}
        >
          🎙️ Record
        </button>
        <button 
          className={`tab-btn ${uploadMode === 'upload' ? 'active' : ''}`}
          onClick={() => setUploadMode('upload')}
        >
          📁 Upload
        </button>
        <button 
          className={`tab-btn ${showTimeline ? 'active' : ''}`}
          onClick={() => setShowTimeline(!showTimeline)}
        >
          🎬 Timeline Studio
        </button>
      </div>

      {showTimeline && (
        <AudioTimeline onTimelineReady={handleTimelineReady} />
      )}

      {!showTimeline && uploadMode === 'record' && (
        <div className="record-mode">
          <div className="recording-visual">
            <div className={`record-indicator ${isRecording ? 'recording' : ''}`}>
              {isRecording ? '🔴' : '⚫'}
            </div>
            <div className="recording-time">
              {formatTime(recordingTime)} / {formatTime(maxDuration)}
            </div>
          </div>

          <div className="recording-controls">
            <button 
              onClick={isRecording ? stopRecording : startRecording}
              className={`record-btn ${isRecording ? 'recording' : ''}`}
              disabled={recordingTime >= maxDuration}
            >
              {isRecording ? '⏹️ Stop Recording' : '🎙️ Start Recording'}
            </button>
          </div>

          {recordedAudio && (
            <div className="audio-preview">
              <h4>📻 Recorded Audio</h4>
              <audio controls src={recordedAudio.url} />
              <div className="preview-controls">
                <button onClick={clearAudio} className="clear-btn">
                  🗑️ Clear
                </button>
                <button onClick={handleSubmit} className="submit-btn">
                  🚀 Submit Recording
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {!showTimeline && uploadMode === 'upload' && (
        <div className="upload-mode">
          <div className="upload-area">
            <input
              ref={fileInputRef}
              type="file"
              accept="audio/*"
              onChange={handleFileUpload}
              className="file-input"
              id="audio-upload"
            />
            <label htmlFor="audio-upload" className="upload-label">
              <div className="upload-content">
                <div className="upload-icon">📁</div>
                <div className="upload-text">
                  <strong>Click to upload audio file</strong>
                  <p>MP3, WAV, M4A, WebM (Max 10MB)</p>
                </div>
              </div>
            </label>
          </div>

          {audioFile && (
            <div className="audio-preview">
              <h4>📻 Uploaded Audio</h4>
              <audio controls src={audioFile.url} />
              <div className="preview-controls">
                <button onClick={clearAudio} className="clear-btn">
                  🗑️ Clear
                </button>
                <button onClick={handleSubmit} className="submit-btn">
                  🚀 Submit Upload
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {timelineData && !showTimeline && (
        <div className="audio-preview">
          <h4>🎵 Timeline Track Ready</h4>
          <p style={{ color: '#00ffff', marginBottom: '1rem' }}>
            Multi-track audio with {timelineData.audio_timeline.length} clips 
            ({Math.floor(timelineData.total_duration)}s total)
          </p>
          <div className="preview-controls">
            <button onClick={clearAudio} className="clear-btn">
              🗑️ Clear
            </button>
            <button onClick={() => setShowTimeline(true)} className="timeline-btn">
              ✏️ Edit Timeline
            </button>
            <button onClick={handleSubmit} className="submit-btn">
              🚀 Submit Track
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// Component: Live Leaderboard (Real-time during voting)
function LiveLeaderboard({ performances }) {
  const sortedPerformances = [...performances].sort((a, b) => 
    (b.average_score || 0) - (a.average_score || 0)
  );

  if (performances.length === 0) {
    return (
      <div className="live-leaderboard">
        <h3>🏆 Live Rankings</h3>
        <p style={{ textAlign: 'center', color: '#666' }}>
          No performances yet
        </p>
      </div>
    );
  }

  return (
    <div className="live-leaderboard">
      <h3>🏆 Live Rankings</h3>
      <div className="live-rankings">
        {sortedPerformances.map((perf, index) => (
          <div key={perf.id} className="live-rank-item">
            <div className="rank-position">
              {index === 0 ? '👑' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${index + 1}`}
            </div>
            <div className="rank-username">{perf.username}</div>
            <div className="rank-score">
              ⭐ {perf.average_score?.toFixed(1) || '0.0'} 
              <span style={{ fontSize: '0.8rem', marginLeft: '0.5rem', color: '#888' }}>
                ({perf.vote_count} votes)
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Component: Home Feed
function HomeFeed({ user, session, onNavigate }) {
  const [feed, setFeed] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [challenges, setChallenges] = useState([]);

  useEffect(() => {
    fetchFeedData();
    const interval = setInterval(fetchFeedData, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const fetchFeedData = async () => {
    try {
      const headers = {
        'Authorization': `Bearer ${session.access_token}`
      };

      const [roomsRes, challengesRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/rooms`, { headers }),
        fetch(`${BACKEND_URL}/api/challenges`, { headers })
      ]);
      
      const roomsData = await roomsRes.json();
      const challengesData = await challengesRes.json();
      
      setRooms(roomsData.rooms || []);
      setChallenges(challengesData.challenges || []);
      
      const feedItems = [
        ...roomsData.rooms.map(room => ({ ...room, type: 'room' })),
        ...challengesData.challenges.map(challenge => ({ ...challenge, type: 'challenge' }))
      ];
      setFeed(feedItems);
    } catch (error) {
      console.error('Error fetching feed:', error);
    }
  };

  return (
    <div className="home-feed">
      <div className="feed-header">
        <h2>🔥 What's Happening</h2>
        <div className="quick-actions">
          <button onClick={() => onNavigate('create-room')} className="create-btn">
            + Create Battle
          </button>
          <button onClick={() => onNavigate('profile')} className="profile-btn">
            {user.username}
          </button>
        </div>
      </div>

      <div className="feed-content">
        {feed.length === 0 ? (
          <div className="empty-feed">
            <h3>🎤 No battles yet!</h3>
            <p>Be the first to create a battle room and start the cypher.</p>
            <button onClick={() => onNavigate('create-room')} className="create-first-btn">
              Create First Battle 🚀
            </button>
          </div>
        ) : (
          feed.map((item) => (
            <div key={item.id} className={`feed-card ${item.type}`}>
              <div className="card-header">
                <div className="card-type">
                  {item.type === 'room' ? '🎤 Battle Room' : '🏆 Challenge'}
                </div>
                <div className={`status-badge ${item.status}`}>
                  {item.status}
                </div>
              </div>
              
              <h3 className="card-title">{item.name || item.title}</h3>
              <p className="card-description">
                {item.prompt || item.description}
              </p>
              
              <div className="card-stats">
                <span className="participants">
                  👥 {item.participants?.length || 0} participants
                </span>
                {item.type === 'room' && item.expires_at && (
                  <span className="expires">
                    ⏰ Expires: {new Date(item.expires_at).toLocaleTimeString()}
                  </span>
                )}
              </div>
              
              <div className="card-actions">
                <button 
                  onClick={() => onNavigate('room', item.id)}
                  className="join-btn"
                  disabled={item.status === 'completed' || item.status === 'closed'}
                >
                  {item.status === 'active' ? 'Join Battle' : 
                   item.status === 'waiting' ? 'Enter Lobby' : 
                   item.status === 'closed' ? 'Battle Ended' :
                   'View Results'}
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// Component: Room/Battle Interface with Live Updates
function BattleRoom({ user, session, roomId, onNavigate }) {
  const [room, setRoom] = useState(null);
  const [timeLeft, setTimeLeft] = useState(300);
  const [phase, setPhase] = useState('create');
  const [performances, setPerformances] = useState([]);
  const [audioSubmitted, setAudioSubmitted] = useState(false);
  const [roomExpired, setRoomExpired] = useState(false);
  
  const timerRef = useRef(null);

  useEffect(() => {
    fetchRoom();
    const interval = setInterval(fetchRoom, 5000); // Update every 5 seconds
    return () => {
      clearInterval(interval);
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [roomId]);

  const fetchRoom = async () => {
    try {
      const headers = {
        'Authorization': `Bearer ${session.access_token}`
      };

      const response = await fetch(`${BACKEND_URL}/api/rooms/${roomId}`, { headers });
      const roomData = await response.json();
      
      if (response.ok) {
        setRoom(roomData);
        
        // Check if room expired
        const expiresAt = new Date(roomData.expires_at);
        const now = new Date();
        if (now > expiresAt || roomData.status === 'closed') {
          setRoomExpired(true);
          setPhase('results');
        }
        
        // Fetch performances
        const perfResponse = await fetch(`${BACKEND_URL}/api/performances/room/${roomId}`, { headers });
        const perfData = await perfResponse.json();
        setPerformances(perfData.performances || []);
        
        // Check if user already submitted
        const userPerf = perfData.performances?.find(p => p.user_id === user.id);
        setAudioSubmitted(!!userPerf);
      }
    } catch (error) {
      console.error('Error fetching room:', error);
    }
  };

  const handleAudioSubmission = async (audioData) => {
    try {
      const perfData = {
        user_id: user.id,
        room_id: roomId,
        audio_data: audioData.audio_data,
        duration: audioData.duration,
        timeline_marks: [],
        audio_timeline: audioData.audio_timeline || []
      };

      const headers = {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json'
      };

      const response = await fetch(`${BACKEND_URL}/api/performances`, {
        method: 'POST',
        headers,
        body: JSON.stringify(perfData)
      });

      if (response.ok) {
        setAudioSubmitted(true);
        fetchRoom();
        alert('🔥 Performance submitted successfully!');
      }
    } catch (error) {
      console.error('Error submitting performance:', error);
      alert('Error submitting performance. Please try again.');
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!room) return <div className="loading">Loading battle room...</div>;

  return (
    <div className="battle-room">
      <div className="room-header">
        <button onClick={() => onNavigate('home')} className="back-btn">← Back</button>
        <div className="room-info">
          <h2>{room.name}</h2>
          {!roomExpired && (
            <div className="timer">
              ⏰ Expires: {new Date(room.expires_at).toLocaleString()}
            </div>
          )}
          {roomExpired && (
            <div className="timer" style={{ color: '#ff4444' }}>
              ⚠️ Battle Ended
            </div>
          )}
        </div>
        <div className="participants">
          👥 {room.participants?.length || 0}/{room.max_participants || 10}
        </div>
      </div>

      <div className="room-content">
        <div className="prompt-section">
          <h3>🎯 Challenge Prompt</h3>
          <p className="prompt-text">{room.prompt}</p>
        </div>

        {/* Live Leaderboard during voting/results */}
        {(phase === 'judge' || phase === 'results' || performances.length > 0) && (
          <LiveLeaderboard performances={performances} />
        )}

        {!roomExpired && !audioSubmitted && (
          <div className="create-phase">
            <h3>🎤 Creation Phase</h3>
            <AudioRecorder 
              onAudioReady={handleAudioSubmission}
              maxDuration={120}
            />
          </div>
        )}

        {audioSubmitted && !roomExpired && (
          <div className="waiting-phase">
            <h3>⏳ Waiting for battle to end...</h3>
            <p>Your performance has been submitted! The battle ends at {new Date(room.expires_at).toLocaleString()}.</p>
          </div>
        )}

        {(roomExpired || phase === 'judge' || phase === 'results') && (
          <div className="judge-phase">
            <h3>⚖️ {roomExpired ? 'Final Results' : 'Judgment Phase'}</h3>
            <div className="performances-list">
              {performances.length === 0 ? (
                <p>No performances to judge yet.</p>
              ) : (
                performances.map((perf, index) => (
                  <PerformanceCard 
                    key={perf.id}
                    performance={perf}
                    user={user}
                    session={session}
                    roomId={roomId}
                    onVote={() => fetchRoom()}
                    canVote={!roomExpired}
                  />
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

// Component: Performance Card with Enhanced Voting
function PerformanceCard({ performance, user, session, roomId, onVote, canVote = true }) {
  const [vote, setVote] = useState({ flow: 5, lyrics: 5, creativity: 5 });
  const [hasVoted, setHasVoted] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    // Check if user already voted for this performance
    const existingVote = performance.votes && performance.votes[user.id];
    setHasVoted(!!existingVote);
  }, [performance.votes, user.id]);

  const submitVote = async () => {
    if (!canVote) {
      alert('Voting is closed for this battle');
      return;
    }

    setIsSubmitting(true);
    try {
      const voteData = {
        voter_id: user.id,
        performance_id: performance.id,
        room_id: roomId,
        ...vote,
        emoji_reaction: '🔥'
      };

      const headers = {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json'
      };

      const response = await fetch(`${BACKEND_URL}/api/votes`, {
        method: 'POST',
        headers,
        body: JSON.stringify(voteData)
      });

      const data = await response.json();
      
      if (response.ok) {
        setHasVoted(true);
        onVote();
        alert('🔥 Vote submitted! Thanks for judging.');
      } else {
        alert(data.detail || 'Error submitting vote');
      }
    } catch (error) {
      console.error('Error submitting vote:', error);
      alert('Error submitting vote. Please try again.');
    }
    setIsSubmitting(false);
  };

  return (
    <div className="performance-card">
      <div className="performance-header">
        <h4>🎤 {performance.username}</h4>
        <div className="average-score">
          ⭐ {performance.average_score?.toFixed(1) || '0.0'}
          <span style={{ fontSize: '0.8rem', marginLeft: '0.5rem' }}>
            ({performance.vote_count || 0} votes)
          </span>
        </div>
      </div>

      {performance.audio_data && performance.audio_data !== 'timeline_placeholder' && (
        <div className="audio-section">
          <audio 
            controls 
            src={`data:audio/webm;base64,${performance.audio_data}`}
          />
        </div>
      )}

      {performance.audio_timeline && performance.audio_timeline.length > 0 && (
        <div className="audio-section">
          <p style={{ color: '#00ffff', marginBottom: '0.5rem' }}>
            🎬 Multi-track composition ({performance.audio_timeline.length} clips)
          </p>
          <div style={{ 
            background: '#1a1a1a', 
            padding: '0.5rem', 
            borderRadius: '5px',
            fontSize: '0.9rem',
            color: '#cccccc'
          }}>
            {performance.audio_timeline.map((clip, i) => (
              <span key={i}>
                🎵 {clip.name}
                {i < performance.audio_timeline.length - 1 ? ' • ' : ''}
              </span>
            ))}
          </div>
        </div>
      )}

      {!hasVoted && performance.user_id !== user.id && canVote && (
        <div className="voting-section">
          <h5>Rate this performance:</h5>
          
          <div className="vote-slider">
            <label>🌊 Flow: {vote.flow}</label>
            <input
              type="range"
              min="1"
              max="10"
              value={vote.flow}
              onChange={(e) => setVote({...vote, flow: parseInt(e.target.value)})}
            />
          </div>

          <div className="vote-slider">
            <label>📝 Lyrics: {vote.lyrics}</label>
            <input
              type="range"
              min="1"
              max="10"
              value={vote.lyrics}
              onChange={(e) => setVote({...vote, lyrics: parseInt(e.target.value)})}
            />
          </div>

          <div className="vote-slider">
            <label>🎨 Creativity: {vote.creativity}</label>
            <input
              type="range"
              min="1"
              max="10"
              value={vote.creativity}
              onChange={(e) => setVote({...vote, creativity: parseInt(e.target.value)})}
            />
          </div>

          <button 
            onClick={submitVote} 
            className="vote-submit-btn"
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Submitting...' : 'Submit Vote 🔥'}
          </button>
        </div>
      )}

      {hasVoted && (
        <div className="voted-message">
          ✅ Vote submitted! Thanks for judging.
        </div>
      )}

      {performance.user_id === user.id && (
        <div className="own-performance">
          🎤 This is your performance
        </div>
      )}

      {!canVote && !hasVoted && performance.user_id !== user.id && (
        <div style={{ 
          textAlign: 'center', 
          color: '#888', 
          padding: '1rem',
          fontStyle: 'italic'
        }}>
          Voting has ended for this battle
        </div>
      )}
    </div>
  );
}

// Component: Leaderboard
function Leaderboard({ user, session, onNavigate }) {
  const [leaderboard, setLeaderboard] = useState([]);

  useEffect(() => {
    fetchLeaderboard();
  }, []);

  const fetchLeaderboard = async () => {
    try {
      const headers = {
        'Authorization': `Bearer ${session.access_token}`
      };
      const response = await fetch(`${BACKEND_URL}/api/users/leaderboard`, { headers });
      const data = await response.json();
      setLeaderboard(data.leaderboard || []);
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
    }
  };

  return (
    <div className="leaderboard">
      <div className="leaderboard-header">
        <button onClick={() => onNavigate('home')} className="back-btn">← Back</button>
        <h2>🏆 Hall of Fame</h2>
      </div>

      <div className="leaderboard-list">
        {leaderboard.length === 0 ? (
          <div className="empty-leaderboard" style={{ textAlign: 'center', padding: '4rem' }}>
            <h3>🏆 No champions yet!</h3>
            <p>Be the first to earn XP and climb the leaderboard.</p>
          </div>
        ) : (
          leaderboard.map((player, index) => (
            <div key={player.id} className={`leaderboard-item ${player.id === user.id ? 'current-user' : ''}`}>
              <div className="rank">
                {index === 0 ? '👑' : index === 1 ? '🥈' : index === 2 ? '🥉' : `#${index + 1}`}
              </div>
              
              <div className="player-info">
                <img src={player.avatar_url} alt={player.username} className="avatar" />
                <div className="player-details">
                  <h3>{player.username}</h3>
                  <div className="player-stats">
                    <span>Level {player.level}</span>
                    <span>•</span>
                    <span>{player.xp} XP</span>
                    <span>•</span>
                    <span>{player.wins}W/{player.battles}B</span>
                  </div>
                </div>
              </div>

              <div className="badges">
                {player.badges?.slice(0, 3).map((badge, i) => (
                  <span key={i} className="badge">🏅 {badge}</span>
                ))}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

// Component: Create Room
function CreateRoom({ user, session, onNavigate }) {
  const [roomData, setRoomData] = useState({
    name: '',
    type: 'challenge',
    prompt: '',
    timer_duration: 300,
    max_participants: 8
  });
  const [isCreating, setIsCreating] = useState(false);

  const handleCreate = async () => {
    if (!roomData.name.trim() || !roomData.prompt.trim()) {
      alert('Please fill in room name and prompt');
      return;
    }

    setIsCreating(true);
    try {
      const headers = {
        'Authorization': `Bearer ${session.access_token}`,
        'Content-Type': 'application/json'
      };

      const response = await fetch(`${BACKEND_URL}/api/rooms`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          ...roomData,
          host_id: user.id
        })
      });

      const newRoom = await response.json();
      if (response.ok) {
        onNavigate('room', newRoom.id);
      } else {
        alert(newRoom.detail || 'Error creating room');
      }
    } catch (error) {
      console.error('Error creating room:', error);
      alert('Error creating room. Please try again.');
    }
    setIsCreating(false);
  };

  return (
    <div className="create-room">
      <div className="create-header">
        <button onClick={() => onNavigate('home')} className="back-btn">← Back</button>
        <h2>🎤 Create Battle Room</h2>
      </div>

      <div className="create-form">
        <div className="form-group">
          <label>Room Name</label>
          <input
            type="text"
            value={roomData.name}
            onChange={(e) => setRoomData({...roomData, name: e.target.value})}
            placeholder="e.g., Friday Night Fires 🔥"
          />
        </div>

        <div className="form-group">
          <label>Battle Type</label>
          <select
            value={roomData.type}
            onChange={(e) => setRoomData({...roomData, type: e.target.value})}
          >
            <option value="challenge">Challenge</option>
            <option value="collab">Collaboration</option>
            <option value="solo">Solo Showcase</option>
          </select>
        </div>

        <div className="form-group">
          <label>Challenge Prompt</label>
          <textarea
            value={roomData.prompt}
            onChange={(e) => setRoomData({...roomData, prompt: e.target.value})}
            placeholder="Give participants a creative challenge..."
            rows="3"
          />
        </div>

        <div className="form-row">
          <div className="form-group">
            <label>Performance Time</label>
            <select
              value={roomData.timer_duration}
              onChange={(e) => setRoomData({...roomData, timer_duration: parseInt(e.target.value)})}
            >
              <option value="60">1 minute</option>
              <option value="120">2 minutes</option>
              <option value="180">3 minutes</option>
              <option value="300">5 minutes</option>
            </select>
          </div>

          <div className="form-group">
            <label>Max Participants</label>
            <select
              value={roomData.max_participants}
              onChange={(e) => setRoomData({...roomData, max_participants: parseInt(e.target.value)})}
            >
              <option value="4">4 people</option>
              <option value="6">6 people</option>
              <option value="8">8 people</option>
              <option value="12">12 people</option>
            </select>
          </div>
        </div>

        <button 
          onClick={handleCreate}
          className="create-submit-btn"
          disabled={!roomData.name || !roomData.prompt || isCreating}
        >
          {isCreating ? 'Creating...' : 'Create Battle Room 🚀'}
        </button>
        
        <p style={{ 
          fontSize: '0.9rem', 
          color: '#888', 
          marginTop: '1rem',
          textAlign: 'center'
        }}>
          ⏰ Room will automatically close after 1 hour
        </p>
      </div>
    </div>
  );
}

// Component: User Profile
function UserProfile({ user, session, onNavigate }) {
  return (
    <div className="user-profile">
      <div className="profile-header">
        <button onClick={() => onNavigate('home')} className="back-btn">← Back</button>
        <button onClick={() => onNavigate('leaderboard')} className="leaderboard-btn">🏆 Leaderboard</button>
      </div>

      <div className="profile-content">
        <div className="profile-card">
          <img src={user.avatar_url} alt={user.username} className="profile-avatar" />
          <h2>{user.username}</h2>
          <p className="bio">{user.bio}</p>
          
          <div className="profile-stats">
            <div className="stat-item">
              <div className="stat-value">{user.level}</div>
              <div className="stat-label">Level</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{user.xp}</div>
              <div className="stat-label">XP</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{user.wins}</div>
              <div className="stat-label">Wins</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{user.battles}</div>
              <div className="stat-label">Battles</div>
            </div>
          </div>

          <div className="xp-progress">
            <div className="progress-bar">
              <div 
                className="progress-fill"
                style={{ width: `${Math.min(100, (user.xp % 1000) / 10)}%` }}
              />
            </div>
            <div className="progress-text">
              {user.xp % 1000}/1000 XP to next level
            </div>
          </div>

          <div className="badges-section">
            <h3>🏅 Badges Earned</h3>
            <div className="badges-grid">
              {user.badges?.length > 0 ? (
                user.badges.map((badge, index) => (
                  <div key={index} className="badge-item">
                    <div className="badge-icon">🏆</div>
                    <div className="badge-name">{badge}</div>
                  </div>
                ))
              ) : (
                <p>No badges earned yet. Start battling to earn your first badge!</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// Main App Component
function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [currentSession, setCurrentSession] = useState(null);
  const [currentView, setCurrentView] = useState('auth');
  const [currentRoomId, setCurrentRoomId] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Check for existing session
    const savedSession = localStorage.getItem('revmix_session');
    if (savedSession) {
      try {
        const session = JSON.parse(savedSession);
        // Verify session is still valid
        fetchCurrentUser(session);
      } catch (error) {
        console.error('Invalid saved session:', error);
        localStorage.removeItem('revmix_session');
        setIsLoading(false);
      }
    } else {
      setIsLoading(false);
    }
  }, []);

  const fetchCurrentUser = async (session) => {
    try {
      const headers = {
        'Authorization': `Bearer ${session.access_token}`
      };
      const response = await fetch(`${BACKEND_URL}/api/users/me`, { headers });
      
      if (response.ok) {
        const userData = await response.json();
        setCurrentUser(userData);
        setCurrentSession(session);
        setCurrentView('home');
      } else {
        localStorage.removeItem('revmix_session');
      }
    } catch (error) {
      console.error('Error fetching current user:', error);
      localStorage.removeItem('revmix_session');
    }
    setIsLoading(false);
  };

  const handleLogin = (user, session) => {
    setCurrentUser(user);
    setCurrentSession(session);
    setCurrentView('home');
  };

  const handleNavigate = (view, data = null) => {
    setCurrentView(view);
    if (view === 'room') {
      setCurrentRoomId(data);
    }
  };

  const handleLogout = async () => {
    try {
      if (currentSession) {
        const headers = {
          'Authorization': `Bearer ${currentSession.access_token}`
        };
        await fetch(`${BACKEND_URL}/api/auth/logout`, {
          method: 'POST',
          headers
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    }
    
    localStorage.removeItem('revmix_session');
    setCurrentUser(null);
    setCurrentSession(null);
    setCurrentView('auth');
    setCurrentRoomId(null);
  };

  if (isLoading) {
    return (
      <div className="loading" style={{ 
        minHeight: '100vh', 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        fontSize: '1.5rem'
      }}>
        🎤 Loading RevMix...
      </div>
    );
  }

  if (!currentUser || !currentSession) {
    return <AuthScreen onLogin={handleLogin} />;
  }

  return (
    <div className="app">
      {currentView === 'home' && (
        <HomeFeed user={currentUser} session={currentSession} onNavigate={handleNavigate} />
      )}
      
      {currentView === 'room' && currentRoomId && (
        <BattleRoom 
          user={currentUser} 
          session={currentSession}
          roomId={currentRoomId} 
          onNavigate={handleNavigate} 
        />
      )}
      
      {currentView === 'leaderboard' && (
        <Leaderboard user={currentUser} session={currentSession} onNavigate={handleNavigate} />
      )}
      
      {currentView === 'create-room' && (
        <CreateRoom user={currentUser} session={currentSession} onNavigate={handleNavigate} />
      )}
      
      {currentView === 'profile' && (
        <UserProfile user={currentUser} session={currentSession} onNavigate={handleNavigate} />
      )}

      <div className="logout-btn" onClick={handleLogout}>
        🚪 Logout
      </div>
    </div>
  );
}

export default App;