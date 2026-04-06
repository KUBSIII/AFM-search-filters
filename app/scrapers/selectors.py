PLAYER_NAME_SELECTORS = [
    "h1",
    ".data-header__headline",
    "[data-testid='headline']",
    "meta[property='og:title']",
]

PROFILE_LABEL_ALIASES = {
    "birth_date": [
        "date of birth",
        "date of birth/age",
        "born",
        "birth date",
    ],
    "position": [
        "position",
        "main position",
    ],
    "contract_expires_at": [
        "contract expires",
        "contract expiration",
        "contract expiry",
    ],
    "agent_name": [
        "agent",
        "player agent",
    ],
    "club_apps": [
        "club appearances",
        "appearances (club)",
        "club apps",
    ],
    "national_team_apps": [
        "national team appearances",
        "national appearances",
        "caps",
        "caps/goals",
        "national team apps",
    ],
    "club_name": [
        "current club",
        "club",
    ],
}
