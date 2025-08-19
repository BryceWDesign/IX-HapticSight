"""
IX-HapticSight — Optical-Haptic Interaction Protocol (OHIP)
Consent Manager (spec §11, §5, §7; culture config in /configs/culture_profiles.yaml)

Purpose
-------
Provide a deterministic, minimal interface for consent handling:
  • Track explicit + policy-based consent with TTL and scopes (e.g., "shoulder_contact")
  • Enforce profile rules: "explicit_only" vs "explicit_or_policy"
  • Generate locale-appropriate announce/consent phrases from a provided phrase bank
  • Expose a single `query(...)` that returns a current ConsentRecord or NONE

Notes
-----
- No file I/O and no external deps. Pass parsed profile/phrase configs in from caller.
- This module does NOT perform speech/gesture recognition; it only records the outcomes.
- PRECONTACT must re-check consent freshness (see spec/state_machine).

See also:
- /configs/culture_profiles.yaml (profiles + phrase_bank)
- /docs/spec.md §11 (Consent Record schema, TTL, scopes)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from time import time
from datetime import datetime, timezone

from .schemas import ConsentRecord, ConsentMode, ConsentSource


# ------------------------- #
#        DATA MODELS        #
# ------------------------- #

@dataclass
class ProfileRules:
    """
    Subset of the culture profile fields we care about for consent logic.
    """
    locale: str = "default"
    language: str = "en"
    social_touch_required_mode: str = "explicit_only"  # "explicit_only" | "explicit_or_policy"
    ttl_seconds: int = 60
    phrase_key: str = "support_request"                # key into phrase_bank
    language_override: Optional[str] = None            # force phrase language if set


# ------------------------- #
#       CONSENT STORE       #
# ------------------------- #

class ConsentManager:
    """
    Tracks consent records and applies profile rules.

    Minimal usage:
        cm = ConsentManager()
        cm.set_profile_from_dict(culture_profiles['profiles']['jp'], defaults=culture_profiles['defaults'])
        cm.enable_institutional_policy(True)  # e.g., clinician/caregiver mode
        cm.grant_explicit("person-1", scopes=["shoulder_contact"], source="verbal")

        rec = cm.query(subject_id="person-1", requested_scopes=["shoulder_contact"])
        # -> ConsentRecord(mode=EXPLICIT, ...)

    For announce phrase:
        phrase = cm.announce_phrase(phrase_bank)
    """

    def __init__(self):
        self._rules = ProfileRules()
        self._institutional_policy_enabled: bool = False  # caregiver/clinician profile switch
        # Store most recent record per subject_id
        self._records: Dict[str, ConsentRecord] = {}

    # ---------- Profile handling ---------- #

    def set_profile_from_dict(self, profile: Dict, defaults: Optional[Dict] = None) -> None:
        """
        Load rules from a culture profile dict (see /configs/culture_profiles.yaml).
        """
        defaults = defaults or {}
        lang = profile.get("language", defaults.get("language", "en"))
        consent_cfg = (profile.get("consent") or {}) or (defaults.get("consent") or {})
        announce_cfg = profile.get("announce") or {}
        self._rules = ProfileRules(
            locale=str(profile.get("name", "")) or "custom",
            language=str(lang),
            social_touch_required_mode=str(consent_cfg.get("social_touch_required_mode", "explicit_only")),
            ttl_seconds=int(consent_cfg.get("ttl_seconds", defaults.get("consent", {}).get("ttl_seconds", 60))),
            phrase_key=str(announce_cfg.get("phrase_key", "support_request")),
            language_override=announce_cfg.get("language_override"),
        )

    def enable_institutional_policy(self, enabled: bool) -> None:
        """
        Toggle caregiver/clinician policy authorization mode.
        When enabled and profile allows "explicit_or_policy", POLICY consent can satisfy social-touch.
        """
        self._institutional_policy_enabled = bool(enabled)

    # ---------- Recording outcomes (UI/ASR/gesture layers call these) ---------- #

    def grant_explicit(self, subject_id: str, scopes: List[str], source: str = "ui",
                       ttl_s: Optional[int] = None) -> ConsentRecord:
        rec = ConsentRecord(
            subject_id=subject_id,
            mode=ConsentMode.EXPLICIT,
            source=ConsentSource(source),
            scope=[s.lower() for s in scopes],
            ttl_s=int(ttl_s if ttl_s is not None else self._rules.ttl_seconds),
        )
        self._records[subject_id] = rec
        return rec

    def grant_policy(self, subject_id: str, scopes: List[str], ttl_s: Optional[int] = None) -> ConsentRecord:
        """
        Record institutionally authorized consent (e.g., caregiver profile).
        Whether it is *sufficient* will be decided by profile rules at query time.
        """
        rec = ConsentRecord(
            subject_id=subject_id,
            mode=ConsentMode.POLICY,
            source=ConsentSource.PROFILE,
            scope=[s.lower() for s in scopes],
            ttl_s=int(ttl_s if ttl_s is not None else self._rules.ttl_seconds),
        )
        self._records[subject_id] = rec
        return rec

    def revoke(self, subject_id: str) -> None:
        self._records.pop(subject_id, None)

    # ---------- Query ---------- #

    def query(self,
              subject_id: str,
              requested_scopes: List[str],
              allow_fallback_policy: Optional[bool] = None) -> ConsentRecord:
        """
        Return a ConsentRecord that reflects current, valid consent for the requested scopes,
        or NONE if insufficient.

        allow_fallback_policy:
            - If None: inferred from profile rules + institutional policy flag.
            - If True: POLICY mode may satisfy when profile is "explicit_or_policy".
            - If False: explicit required regardless of policy flag.
        """
        requested = {s.lower() for s in requested_scopes}
        now = time()
        rule_mode = self._rules.social_touch_required_mode
        allow_policy = (
            self._institutional_policy_enabled and rule_mode == "explicit_or_policy"
            if allow_fallback_policy is None else bool(allow_fallback_policy)
        )

        rec = self._records.get(subject_id)

        # Validate record freshness and scope
        def _valid(r: ConsentRecord) -> bool:
            if not r.is_active(now):
                return False
            scopes = {s.lower() for s in (r.scope or [])}
            return requested.issubset(scopes)

        # 1) Prefer explicit if valid
        if rec and rec.mode == ConsentMode.EXPLICIT and _valid(rec):
            return rec

        # 2) Fall back to policy only if allowed by rules and enabled
        if allow_policy and rec and rec.mode == ConsentMode.POLICY and _valid(rec):
            return rec

        # 3) Otherwise, return NONE record with minimal info
        return ConsentRecord(
            subject_id=subject_id,
            mode=ConsentMode.NONE,
            source=ConsentSource.UI,
            scope=list(requested),
            ttl_s=self._rules.ttl_seconds,
        )

    # ---------- Announce phrase ---------- #

    def announce_phrase(self, phrase_bank: Dict[str, Dict[str, str]]) -> str:
        """
        Select a phrase for requesting consent/announcing intent.
        phrase_bank format:
            { phrase_key: { lang_code: phrase, ... } }
        Falls back gracefully to English if missing locale entries.
        """
        key = self._rules.phrase_key or "support_request"
        lang = (self._rules.language_override or self._rules.language or "en").lower()
        entry = phrase_bank.get(key, {})
        return entry.get(lang) or entry.get("en") or "May I proceed?"

    # ---------- Introspection ---------- #

    @property
    def rules(self) -> ProfileRules:
        return self._rules

    @property
    def institutional_policy_enabled(self) -> bool:
        return self._institutional_policy_enabled
