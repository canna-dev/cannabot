# 🌿 CannaBot - Cannabis Tracker Discord Bot

A streamlined Discord bot for cannabis consumption tracking with real strain data from Leafly. Features bioavailability-based THC calculations, comprehensive strain database, and user-friendly interface.

## ✨ Features

### � **Ultra-Simplified Interface**
- **Only 5 essential commands** - Maximum user-friendliness
- **Real Leafly data** - 4,762+ cannabis strains with effects, THC levels, and descriptions
- **Smart bioavailability** - Accurate THC absorption calculations
- **Comprehensive help** - Built-in documentation and examples

### 🌿 **Core Commands**
1. **`/use`** - Log cannabis consumption (all methods in one command)
2. **`/strains`** - Search 4,762+ Leafly strains with effects matching
3. **`/stash`** - Manage your cannabis inventory  
4. **`/stats`** - View consumption analytics and trends
5. **`/help`** - Comprehensive help with examples

### 📊 **Accurate Calculations**
Based on peer-reviewed bioavailability research:

| Method     | Bioavailability | Example (1g) |
|------------|----------------|--------------|
| Smoking    | 30%            | 6.0mg THC    |
| Vaping     | 50%            | 10.0mg THC   |
| Dabbing    | 75%            | 15.0mg THC   |
| Edibles    | 15%            | 3.0mg THC    |
| Tinctures  | 35%            | 7.0mg THC    |
| Capsules   | 20%            | 4.0mg THC    |

### 🔍 **Real Strain Database**
- **4,762 Leafly strains** with complete profiles (98 with premium images)
- **Effect percentages** - Relaxed, Happy, Euphoric, Creative, etc.
- **THC/CBD levels** - Accurate potency information  
- **Medical applications** - Symptom relief data
- **Strain discovery** - Find strains by desired effects
- **Visual strain guide** - Premium Leafly images for top strains

## 🚀 Future Roadmap

### 🌿 **Strain Database Expansion** (2025-2026)
- **🔍 Enhanced Discovery** - Advanced filtering by terpene profiles, breeding lineage, and region
- **📈 Real-time Updates** - Dynamic strain database with weekly Leafly synchronization
- **🌍 Global Strains** - Integration with international databases (Europe, Canada, Australia)
- **👥 Community Strains** - User-submitted strain reviews and custom strain profiles
- **🧬 Genetics Tracking** - Detailed parent/child strain relationships and breeding history

### 📸 **Visual Experience** (Q1 2026)
- **🖼️ Strain Gallery** - High-quality images in all strain embeds (Currently Available!)
- **📊 Visual Analytics** - Interactive charts for consumption patterns and strain preferences
- **🎨 Custom Themes** - Personalized bot appearance with strain-inspired color schemes
- **📱 Mobile Optimization** - Enhanced Discord mobile experience

### 🤖 **AI Integration** (Q2 2026)
- **🧠 Smart Recommendations** - AI-powered strain suggestions based on consumption history
- **💬 Natural Language** - Chat with CannaBot about strains using natural language
- **🔮 Effect Prediction** - Personalized effect forecasting based on individual tolerance
- **📝 Automated Journaling** - AI-generated consumption insights and patterns

### 🏥 **Medical Features** (Q3 2026)
- **💊 Dosage Calculator** - Advanced medical dosing with doctor consultation integration
- **🩺 Symptom Tracking** - Comprehensive medical cannabis effect monitoring
- **👨‍⚕️ Healthcare Integration** - Optional sharing with medical professionals
- **📋 Medical Reports** - Automated reports for medical cannabis programs

### 🌐 **Community & Social** (Q4 2026)
- **👥 Strain Communities** - Connect with users who enjoy similar strains
- **🏆 Achievement System** - Badges for strain exploration and responsible usage
- **📱 Mobile App** - Dedicated iOS/Android companion app
- **🌍 Localization** - Multi-language support (Spanish, French, German, Portuguese)

### 🔬 **Advanced Analytics** (2027)
- **🧪 Terpene Matching** - Deep terpene profile analysis and recommendations
- **💡 Micro-dosing Tools** - Precision tools for micro-dose tracking and optimization
- **🔄 Cross-platform Sync** - Integration with cannabis tracking apps and devices
- **📊 Research Partnership** - Contribute anonymized data to cannabis research (opt-in)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Discord Bot Token
- Git

### Installation Options

#### 🐳 **Docker (Recommended)**
```bash
git clone https://github.com/yourusername/CannaBot.git
cd CannaBot
cp .env.docker .env
# Edit .env with your Discord token
./docker-start.sh  # Linux/Mac
# OR
docker-start.bat   # Windows
```

#### 🐍 **Python Installation**

1. **Clone and setup**
   ```bash
   git clone https://github.com/yourusername/CannaBot.git
   cd CannaBot
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   # Create .env file
   DISCORD_TOKEN=your_bot_token_here
   DEBUG=true
   LOG_LEVEL=INFO
   DATABASE_URL=sqlite:///cannabot.db
   ```

3. **Run the bot**
   ```bash
   python run_bot.py
   ```

## 📱 Usage Examples

### Log Consumption
```
/use method:smoke amount:1.5 strain:Blue Dream
```
> 🌿 **Smoke Session Logged!**
> 
> **Method:** Smoke  
> **Amount:** 1.5g  
> **Effective THC:** 9.0mg (30% bioavailability)  
> **Strain:** Blue Dream (Hybrid)

### Find Strains by Effects
```
/strains effects:creative
```
> 🧠 **Top Creative Strains:** (with strain images)
> 
> 1. **Green Crack** (Sativa) - 85% Creative  
> 2. **Durban Poison** (Sativa) - 80% Creative  
> 3. **Jack Herer** (Hybrid) - 75% Creative
> 
> *Featuring high-quality Leafly strain images*

### Check Your Stats
```
/stats period:week
```
> 📊 **Weekly Stats**
> 
> **Total Sessions:** 12  
> **Total THC:** 84.5mg  
> **Favorite Method:** Vaping (60%)  
> **Top Strain:** Blue Dream (4 sessions)

## 🏗️ Project Structure

```
CannaBot/
├── bot/
│   ├── main.py                 # Bot entry point
│   ├── config.py              # Configuration management  
│   ├── commands/
│   │   ├── core.py            # All 5 essential commands
│   │   └── unused_backup/     # Original 31 command files (backup)
│   ├── database/              # Database models and operations
│   ├── services/              # Business logic
│   └── utils/                 # Utility functions
├── data/
│   └── leafly_strain_data.csv # 4,762 Leafly strain database
├── tests/                     # Test suite
├── docs/                      # Documentation
├── requirements.txt           # Dependencies
└── README.md
```

## 🧪 Testing

Run the simple test suite:
```bash
python tests/test_simple.py
```

For full testing with pytest:
```bash
pip install pytest pytest-asyncio
python -m pytest tests/ -v
```

## 🔧 Configuration

### Environment Variables
```env
# Required
DISCORD_TOKEN=your_bot_token_here

# Optional  
DEBUG=true                           # Enable debug mode
LOG_LEVEL=INFO                       # Logging level
DATABASE_URL=sqlite:///cannabot.db   # Database connection
DISCORD_GUILD_ID=123456789           # Test guild ID (development)
```

### Database
- **Development:** SQLite (automatic setup)
- **Production:** PostgreSQL recommended
- **Migrations:** Automatic on startup

## � Documentation

### Command Reference
- **`/use`** - Universal consumption logging for all methods
- **`/strains`** - Search and discover from 4,762+ Leafly strains  
- **`/stash`** - Inventory management with automatic depletion
- **`/stats`** - Analytics with bioavailability-accurate calculations
- **`/help`** - Interactive help with 8 sections and 15+ examples

### Strain Database Features
- **Search by name** - Find specific strains
- **Filter by effects** - Match desired experiences
- **Random discovery** - Explore new strains
- **Effect percentages** - Data-driven selection
- **Medical applications** - Symptom relief matching

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow async/await patterns
- Add tests for new functionality
- Update documentation
- Use type hints
- Follow PEP 8 style guide

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This bot is for educational and personal use in jurisdictions where cannabis is legal. Users must comply with local laws. The bot provides informational calculations only and is not medical advice.

## 🆘 Support

- **Issues:** [GitHub Issues](https://github.com/yourusername/CannaBot/issues)
- **Discussions:** [GitHub Discussions](https://github.com/yourusername/CannaBot/discussions)
- **Discord:** Join our support server

---

**Made with 🌿 for the cannabis community**
