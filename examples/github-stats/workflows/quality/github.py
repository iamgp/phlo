"""Quality checks for GitHub data using @phlo.quality decorator.

Demonstrates phlo's declarative quality check framework with multiple check types.
"""

import phlo
from phlo.quality import CountCheck, NullCheck, PatternCheck, RangeCheck, SchemaCheck, UniqueCheck

from workflows.schemas.github import RawUserEvents


@phlo.quality(
    table="raw.user_events",
    checks=[
        NullCheck(columns=["id", "type", "created_at"]),
        UniqueCheck(columns=["id"]),
        SchemaCheck(schema=RawUserEvents),
        CountCheck(min_rows=1),
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
        UniqueCheck(columns=["id"]),
        RangeCheck(column="stargazers_count", min_value=0, max_value=1000000),
        RangeCheck(column="forks_count", min_value=0, max_value=100000),
        CountCheck(min_rows=1),
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
        UniqueCheck(columns=["id"]),
        PatternCheck(
            column="login", pattern=r"^[a-zA-Z0-9](?:[a-zA-Z0-9]|-(?=[a-zA-Z0-9])){0,38}$"
        ),
        RangeCheck(column="followers", min_value=0, max_value=1000000),
        RangeCheck(column="following", min_value=0, max_value=10000),
    ],
    group="github",
    blocking=True,
)
def user_profile_quality():
    """Quality checks for GitHub user profile."""
    pass
