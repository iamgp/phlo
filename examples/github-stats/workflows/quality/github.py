"""Quality checks for GitHub data using @phlo.quality decorator.

Implements data quality assurance for GitHub events and repository data.
"""

import phlo
from phlo.quality import NullCheck, RangeCheck


@phlo.quality(
    table="raw.user_events",
    checks=[
        NullCheck(columns=["id", "type", "created_at"]),
    ],
    group="github",
    blocking=True,
)
def user_events_quality():
    """Quality checks for GitHub user events."""
    pass


@phlo.quality(
    table="raw.user_repos",
    checks=[
        NullCheck(columns=["id", "name", "created_at"]),
        RangeCheck(column="stargazers_count", min_value=0, max_value=1000000),
        RangeCheck(column="forks_count", min_value=0, max_value=100000),
    ],
    group="github",
    blocking=True,
)
def user_repos_quality():
    """Quality checks for GitHub repositories."""
    pass


@phlo.quality(
    table="raw.user_profile",
    checks=[
        NullCheck(columns=["id", "login"]),
        RangeCheck(column="followers", min_value=0, max_value=1000000),
        RangeCheck(column="following", min_value=0, max_value=10000),
    ],
    group="github",
    blocking=True,
)
def user_profile_quality():
    """Quality checks for GitHub user profile."""
    pass
