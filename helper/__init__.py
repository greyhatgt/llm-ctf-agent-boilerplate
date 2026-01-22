"""
Helper module for CTF Agent integration
Includes CTFd and CTFTime compatibility
"""

from helper.legacy_ctf_challenge import (
    CTFChallenge,
    CTFdChallenge,
    CTFTimeChallenge,
    CTFdClient,
    CTFTimeHelper,
    CTFChallenge,
    ChallengeFiles,
    ChallengeHint,
)

from helper.ctftime_helper import (
    CTFTimeEndpoint,
    CTFTimeHelper,
    get_active_challenges_from_ctftime,
    sync_ctftime_to_local,
)

__all__ = [
    'CTFChallenge',
    'CTFdChallenge',
    'CTFTimeChallenge',
    'CTFdClient',
    'CTFTimeHelper',
    'CTFChallenge',
    'ChallengeFiles',
    'ChallengeHint',
    'CTFTimeEndpoint',
    'get_active_challenges_from_ctftime',
    'sync_ctftime_to_local',
]

