"""agent-reach social media integration for AI Chaos Scout.

This source adapter dynamically probes for social media scraping tools 
(like twitter-cli or OpenCLI) using the bundled `agent-reach` extension.
If a tool is missing or unauthenticated, it raises an AgentReachConfigurationError
which is caught by run_scout.py and appended to `setup_warnings`.
"""

from __future__ import annotations

import json
import subprocess
from scout.models import Item
from scout.state import State
from scout.sources._util import to_iso_utc, excerpt

class AgentReachConfigurationError(Exception):
    pass

def _fetch_twitter(queries: list[str]) -> list[Item]:
    try:
        from scout.ext.agent_reach.channels.twitter import TwitterChannel
    except ImportError:
        return []
    
    chan = TwitterChannel()
    status, msg = chan.check()
    if status in ("warn", "error", "off"):
        raise AgentReachConfigurationError(f"[Twitter] {msg}")
    
    items = []
    backend = getattr(chan, "active_backend", None)
    
    for query in queries:
        if not query.strip(): continue
        
        if backend == "twitter-cli":
            cmd = ["twitter", "search", query, "--limit", "10", "--json"]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if res.returncode == 0:
                    for line in res.stdout.strip().splitlines():
                        try:
                            tweet = json.loads(line)
                            items.append(Item.create(
                                source="reach_twitter",
                                url=tweet.get("url") or f"https://x.com/i/status/{tweet.get('id')}",
                                title=f"Tweet from {tweet.get('username', 'Unknown')}",
                                excerpt=excerpt(tweet.get("text", "")),
                                published_at=to_iso_utc(tweet.get("created_at")),
                            ))
                        except Exception:
                            pass
            except Exception:
                pass
        elif backend == "OpenCLI":
            cmd = ["opencli", "twitter", "search", query, "-f", "json"]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if res.returncode == 0:
                    data = json.loads(res.stdout)
                    for t in (data if isinstance(data, list) else []):
                        items.append(Item.create(
                            source="reach_twitter",
                            url=t.get("url", ""),
                            title=t.get("text", "")[:50],
                            excerpt=excerpt(t.get("text", ""))
                        ))
            except Exception:
                pass

    return items

def _fetch_bilibili(queries: list[str]) -> list[Item]:
    try:
        from scout.ext.agent_reach.channels.bilibili import BilibiliChannel
    except ImportError:
        return []
    
    chan = BilibiliChannel()
    status, msg = chan.check()
    if status in ("warn", "error", "off"):
        raise AgentReachConfigurationError(f"[Bilibili] {msg}")
    
    items = []
    backend = getattr(chan, "active_backend", None)
    for query in queries:
        if not query.strip(): continue
        if backend == "bili-cli":
            cmd = ["bili", "search", query, "--json"]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                if res.returncode == 0:
                    data = json.loads(res.stdout)
                    for v in data.get("result", []):
                        items.append(Item.create(
                            source="reach_bilibili",
                            url=v.get("arcurl", ""),
                            title=v.get("title", "").replace("<em class=\"keyword\">", "").replace("</em>", ""),
                            excerpt=excerpt(v.get("description", ""))
                        ))
            except Exception:
                pass
    return items

def fetch(config: dict, state: State) -> list[Item]:
    items: list[Item] = []
    
    # Twitter
    tw_queries = config.get("reach_twitter", [])
    if tw_queries:
        items.extend(_fetch_twitter(tw_queries))
        
    # Bilibili
    bili_queries = config.get("reach_bilibili", [])
    if bili_queries:
        items.extend(_fetch_bilibili(bili_queries))
        
    return items
