# 🎤 RevMix - Real-Time Audio Battle Platform

**Where Bars Battle & Beats Drop**

RevMix is a cutting-edge, real-time audio-first mobile application where users create live music parties, perform verses, compete in battles, and get judged by live audiences. Built with modern tech stack featuring black & cyan theme, advanced audio timeline studio, and comprehensive battle management.

## ✨ Features

### 🎵 Core Battle System
- **Real-time Audio Battles** - Live performance rooms with 1-hour auto-expiry
- **Multi-track Audio Studio** - Drag & drop timeline with built-in effects
- **Live Voting System** - Real-time judgment with flow/lyrics/creativity scoring
- **Progressive XP System** - Level up, earn badges, climb leaderboards
- **Room Management** - Auto-close battles, announce results, award XP

### 🎬 Audio Timeline Studio
- **Drag & Drop Interface** - Build multi-track compositions
- **Built-in Effects Library** - Boom, Applause, Air Horn, Vinyl Scratch
- **Custom Audio Uploads** - Add your own samples and effects
- **Real-time Preview** - Play and edit timeline before submission
- **Multi-clip Compositions** - Combine multiple audio elements

### ⚖️ Enhanced Voting & Results
- **Prevent Multiple Votes** - One vote per user per performance
- **Live Leaderboard** - Real-time rankings during voting
- **Results Announcement** - Automatic winner selection and XP awards
- **Vote Restrictions** - Cannot vote for own performances

### 🔐 Authentication & Security
- **Supabase Integration** - Real username/password authentication
- **Session Management** - Persistent login with secure token storage
- **User Profiles** - Comprehensive stats, badges, and progress tracking

## 🛠️ Tech Stack

### Backend
- **FastAPI** - High-performance Python web framework
- **MongoDB** - Document database for flexible data storage
- **Supabase** - Authentication and user management
- **APScheduler** - Automated room cleanup and result processing

### Frontend
- **React** - Modern UI library with hooks
- **Supabase JS** - Client-side authentication integration
- **CSS3** - Custom black & cyan theme with animations
- **Web Audio API** - Browser-based audio recording and playback

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ and Yarn
- Python 3.11+ and pip
- MongoDB running locally
- Supabase account and project

### Installation

1. **Clone and Setup**
   ```bash
   cd /app
   ```

2. **Backend Setup**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   yarn install
   ```

4. **Environment Configuration**
   
   Backend `.env`:
   ```env
   MONGO_URL="mongodb://localhost:27017"
   DB_NAME="revmix_production"
   SUPABASE_URL="https://your-project.supabase.co"
   SUPABASE_ANON_KEY="your-anon-key"
   SUPABASE_SERVICE_KEY="your-service-key"
   ```

   Frontend `.env`:
   ```env
   REACT_APP_BACKEND_URL=https://your-backend-url
   REACT_APP_SUPABASE_URL=https://your-project.supabase.co
   REACT_APP_SUPABASE_ANON_KEY=your-anon-key
   ```

5. **Start Services**
   ```bash
   sudo supervisorctl restart all
   ```

## 📱 Application Flow

### 1. Authentication
- **Register**: Username, email, password
- **Login**: Username + password authentication
- **Session**: Persistent login with token storage

### 2. Battle Creation
- **Create Room**: Name, prompt, type, duration, max participants
- **Auto-Expiry**: Rooms automatically close after 1 hour
- **Join Battles**: Enter lobby and participate in active battles

### 3. Audio Creation
- **Record Live**: Browser-based audio recording up to 2 minutes
- **Upload Files**: Support for MP3, WAV, M4A, WebM (max 10MB)
- **Timeline Studio**: Multi-track composition with drag & drop
- **Built-in Effects**: Professional audio effects library

### 4. Competition & Voting
- **Submit Performance**: Audio with optional timeline data
- **Live Rankings**: Real-time leaderboard during voting
- **Fair Voting**: One vote per user, cannot vote for own performance
- **Scoring System**: Flow (1-10), Lyrics (1-10), Creativity (1-10)

### 5. Results & Progression
- **Auto Results**: Automatic winner announcement when room expires
- **XP Awards**: 100 XP for winners, 25 XP for participants
- **Badge System**: Earn badges like "Battle Winner", "Newcomer"
- **Leaderboards**: Global rankings by XP and wins

## 🎨 Design System

### Color Scheme
- **Primary**: Cyan (#00ffff) - Main accent color
- **Secondary**: Blue (#00aaff) - Gradients and highlights
- **Background**: Black (#000000) - Primary background
- **Surface**: Dark Gray (#1a1a1a) - Cards and containers
- **Text**: White (#ffffff) - Primary text
- **Accent**: Gray (#cccccc) - Secondary text

### Typography
- **Font Family**: Inter, system fonts
- **Headers**: Bold weights with cyan color
- **Body**: Regular weights with white/gray colors
- **Interactive**: Hover effects and transitions

## 🔧 API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

### Users
- `GET /api/users/me` - Get current user profile
- `GET /api/users/profile/{user_id}` - Get user profile
- `GET /api/users/leaderboard` - Get leaderboard

### Rooms
- `GET /api/rooms` - Get active rooms
- `GET /api/rooms/{room_id}` - Get room details
- `POST /api/rooms` - Create new room
- `POST /api/rooms/{room_id}/join` - Join room
- `POST /api/rooms/{room_id}/close` - Close room (host only)
- `GET /api/rooms/{room_id}/results` - Get room results

### Performances
- `POST /api/performances` - Submit performance
- `GET /api/performances/room/{room_id}` - Get room performances

### Voting
- `POST /api/votes` - Submit vote
- `GET /api/votes/performance/{performance_id}` - Get performance votes

### Audio Effects
- `GET /api/audio-effects` - Get available effects
- `POST /api/audio-effects` - Upload custom effect

## 🏗️ Architecture

### Database Schema

**Users Collection**
```javascript
{
  id: String,
  username: String (unique),
  email: String,
  supabase_id: String,
  level: Number,
  xp: Number,
  wins: Number,
  battles: Number,
  badges: [String],
  created_at: Date
}
```

**Rooms Collection**
```javascript
{
  id: String,
  name: String,
  host_id: String,
  type: String, // solo, collab, challenge
  prompt: String,
  participants: [String],
  status: String, // waiting, active, completed, closed
  created_at: Date,
  expires_at: Date, // 1 hour from creation
  max_participants: Number,
  winner_id: String
}
```

**Performances Collection**
```javascript
{
  id: String,
  user_id: String,
  username: String,
  room_id: String,
  audio_data: String, // base64
  duration: Number,
  audio_timeline: [Object], // multi-track data
  votes: Object, // {user_id: {flow, lyrics, creativity}}
  average_score: Number,
  vote_count: Number,
  submitted_at: Date
}
```

### Security Features
- **JWT Authentication** - Supabase-based token validation
- **Rate Limiting** - Prevent vote spamming
- **Input Validation** - All user inputs sanitized
- **CORS Configuration** - Secure cross-origin requests

## ⚡ Performance Optimizations

### Backend
- **Database Indexes** - Optimized queries for users, rooms, performances
- **Background Jobs** - Automated room cleanup every 5 minutes
- **Async Operations** - Non-blocking database operations
- **Connection Pooling** - Efficient MongoDB connections

### Frontend
- **Real-time Updates** - Live data refresh every 5-10 seconds
- **Optimistic UI** - Immediate feedback for user actions
- **Code Splitting** - Efficient bundle loading
- **Audio Optimization** - Compressed base64 storage

## 🧪 Testing

### Backend Testing
```bash
# Run comprehensive backend tests
python -m pytest backend_test.py -v
```

### Frontend Testing
- Manual testing of all user flows
- Audio recording/playbook functionality
- Real-time voting and leaderboard updates
- Authentication and session management

## 🚀 Deployment

### Production Considerations
- **Environment Variables** - Secure API key management
- **Database Scaling** - MongoDB Atlas for production
- **CDN Integration** - Static asset optimization
- **Monitoring** - Application performance tracking

### Docker Support
```dockerfile
# Backend Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8001"]
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🎯 Roadmap

### Phase 1 (Completed) ✅
- ✅ Real-time audio battles
- ✅ Authentication system
- ✅ Voting and scoring
- ✅ Audio timeline studio
- ✅ Black & cyan theme
- ✅ Room lifecycle management

### Phase 2 (Future)
- 🔄 LiveKit integration for real-time streams
- 🔄 AI pitch detection and scoring
- 🔄 Advanced audio effects
- 🔄 Push notifications
- 🔄 Social features and friend systems
- 🔄 Tournament brackets

### Phase 3 (Future)
- 🔄 Mobile apps (iOS/Android)
- 🔄 Streaming integration
- 🔄 Monetization features
- 🔄 Analytics dashboard

## 📞 Support

For support, email support@revmix.app or join our Discord community.

---

**Built with ❤️ for the hip-hop community**

🎤 *"Every great rapper started with their first bar"* 🎤
