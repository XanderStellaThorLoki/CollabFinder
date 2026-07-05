"""Turn message text into topic signals.

Deliberately simple: lowercase, strip Slack markup, extract unigrams and
bigrams, drop stopwords. Good enough to cluster expertise in a hackathon
corpus; swappable for embeddings later without touching anything upstream
or downstream (the contract is text -> list of topic terms).
"""

from __future__ import annotations

import re

STOPWORDS = {
    "a", "about", "after", "all", "an", "and", "any", "anyone", "are", "as", "at",
    "be", "been", "before", "below", "but", "by", "can", "could", "did", "do",
    "does", "doing", "done", "down", "for", "from", "get", "gets", "getting",
    "got", "had", "has", "have", "having", "here", "hi", "how", "i", "if", "in",
    "into", "is", "it", "its", "just", "know", "like", "me", "more", "most",
    "my", "need", "needs", "new", "no", "not", "now", "of", "on", "one", "only",
    "or", "our", "out", "over", "please", "so", "some", "than", "that", "the",
    "their", "them", "then", "there", "these", "they", "this", "to", "today",
    "too", "up", "us", "use", "used", "using", "very", "want", "was", "we",
    "were", "what", "when", "where", "which", "who", "why", "will", "with",
    "would", "you", "your", "yes", "yeah", "ok", "okay", "thanks", "thank",
    "week", "month", "quarter", "friday", "monday", "tuesday", "thursday",
    "morning", "afternoon", "team", "everyone", "anyone", "someone", "way",
    "last", "next", "first", "still", "also", "im", "ive", "dont", "cant",
    "heres", "whats", "lets", "etc", "eod", "tldr", "fyi", "psa",
}

_SLACK_MARKUP = re.compile(r"<[^>]+>")          # mentions, links, channel refs
_NON_WORD = re.compile(r"[^a-z0-9\-\s]")


def extract_topics(text: str) -> list[str]:
    """Return topic terms (unigrams + bigrams) for one message."""
    cleaned = _SLACK_MARKUP.sub(" ", text.lower())
    cleaned = _NON_WORD.sub(" ", cleaned)
    words = [w for w in cleaned.split() if len(w) > 1]

    unigrams = [w for w in words if w not in STOPWORDS]
    bigrams = [
        f"{a} {b}"
        for a, b in zip(words, words[1:])
        if a not in STOPWORDS and b not in STOPWORDS
    ]
    return unigrams + bigrams
