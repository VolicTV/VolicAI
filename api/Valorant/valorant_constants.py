"""Constants used across the Valorant integration"""

# Rank Icons and Tiers
RANKS = {
    "Iron 1": "🔨1",
    "Iron 2": "🔨2",
    "Iron 3": "🔨3",
    "Bronze 1": "🥉1",
    "Bronze 2": "🥉2",
    "Bronze 3": "🥉3",
    "Silver 1": "⚔️1",
    "Silver 2": "⚔️2",
    "Silver 3": "⚔️3",
    "Gold 1": "🏅1",
    "Gold 2": "🏅2",
    "Gold 3": "🏅3",
    "Platinum 1": "💎1",
    "Platinum 2": "💎2",
    "Platinum 3": "💎3",
    "Diamond 1": "💠1",
    "Diamond 2": "💠2",
    "Diamond 3": "💠3",
    "Ascendant 1": "🔱1",
    "Ascendant 2": "🔱2",
    "Ascendant 3": "🔱3",
    "Immortal 1": "👑1",
    "Immortal 2": "👑2",
    "Immortal 3": "👑3",
    "Radiant": "⚡"
}

# Map Icons
MAPS = {
    "Ascent": "🏰",
    "Bind": "🏜️",
    "Haven": "🏯",
    "Split": "🌆",
    "Icebox": "❄️",
    "Breeze": "🏖️",
    "Fracture": "💥",
    "Pearl": "🌊",
    "Lotus": "🌸",
    "Sunset": "🌅"
}

# Agent Icons
AGENTS = {
    "Jett": "💨",
    "Raze": "💣",
    "Breach": "🤜",
    "Omen": "👻",
    "Brimstone": "🎯",
    "Phoenix": "🔥",
    "Sage": "🧊",
    "Sova": "🏹",
    "Viper": "☠️",
    "Cypher": "🕵️",
    "Reyna": "👁️",
    "Killjoy": "🤖",
    "Skye": "🦊",
    "Yoru": "⚡",
    "Astra": "✨",
    "KAY/O": "🤖",
    "Chamber": "🎩",
    "Neon": "⚡",
    "Fade": "👻",
    "Harbor": "🌊",
    "Gekko": "🦎",
    "Deadlock": "🔒",
    "Iso": "🎭"
}

# API Endpoints
API_ENDPOINTS = {
    "ACCOUNT": "/account",
    "MMR": "/mmr",
    "MATCHES": "/matches",
    "CONTENT": "/content"
}

# Cache Durations (in seconds)
CACHE_DURATIONS = {
    "ACCOUNT": 86400,  # 24 hours
    "MMR": 300,       # 5 minutes
    "MATCHES": 300,   # 5 minutes
    "CONTENT": 86400  # 24 hours
}

# Game Modes
GAME_MODES = {
    "Competitive": "🏆",
    "Unrated": "🎮",
    "Spike Rush": "💣",
    "Deathmatch": "💀",
    "Escalation": "📈",
    "Replication": "🔄",
    "Custom": "⚙️",
    "Swiftplay": "⚡"
}

# Weapon Categories
WEAPON_CATEGORIES = {
    "Sidearm": "🔫",
    "SMG": "🔫",
    "Shotgun": "🔫",
    "Rifle": "🎯",
    "Sniper": "🎯",
    "Heavy": "💥",
    "Melee": "🗡️"
}

# Performance Indicators
PERFORMANCE_INDICATORS = {
    "excellent": "🌟",
    "good": "✅",
    "average": "➖",
    "poor": "❌"
}

# Time Periods
TIME_PERIODS = {
    "morning": "🌅",
    "afternoon": "☀️",
    "evening": "🌆",
    "night": "🌙"
}

# Error Messages
ERROR_MESSAGES = {
    "API_ERROR": "An error occurred while fetching data from the Valorant API",
    "INVALID_RIOT_ID": "Invalid Riot ID format. Must be name#tag",
    "USER_NOT_FOUND": "Could not find user with the provided Riot ID",
    "NO_MATCHES": "No recent matches found for this player",
    "NO_STATS": "No statistics available for this player",
    "RATE_LIMIT": "Rate limit exceeded. Please try again later",
    "CACHE_ERROR": "Error accessing cached data",
    "GENERAL_ERROR": "An unexpected error occurred"
}

# Command Cooldowns (in seconds)
COMMAND_COOLDOWNS = {
    "rank": 60,
    "stats": 60,
    "matches": 60,
    "profile": 300
}

# Default Values
DEFAULTS = {
    "NUM_MATCHES": 3,
    "MAX_MATCHES": 10,
    "CACHE_SIZE": 1000,
    "MAX_RETRIES": 3,
    "TIMEOUT": 10
}