# Owner: Nikki
"""Failover across the (key, model) pool, tested without any real key.

The point of building this before the keys exist is that the behaviour can be
pinned down now: the day it matters is the demo, in front of judges, and the
failure it guards against — a spent daily quota — cannot be reproduced on
demand with real keys either. A stub that raises RESOURCE_EXHAUSTED when told
to is a better test than five real accounts.

What is being asserted is mostly about NOT doing things: not retrying a spent
combination, not going back to key 1, not burning a key on a network blip, not
counting five slots when three are filled.
"""

import logging
import unittest

from ai.adapters.base import AllProvidersExhausted
from ai.adapters.keypool import GeminiKeyPool, collect_keys, collect_models

KEYS = [f"key-value-{n}" for n in range(1, 6)]
PRIMARY = "primary-model"
FALLBACK = "fallback-model"


class QuotaError(Exception):
    """Shaped like the SDK's: the signal is in the message text."""

    def __init__(self, message="429 RESOURCE_EXHAUSTED: quota exceeded for this project"):
        super().__init__(message)


class StubModel:
    """Stands in for a configured Gemini model. Records what it was asked."""

    def __init__(self, key, model_name, pool):
        self.key = key
        self.model_name = model_name
        self._pool = pool

    def generate_content(self, prompt):
        self._pool.calls.append((self.key, self.model_name))
        if (self.key, self.model_name) in self._pool.dead:
            raise QuotaError()
        if self._pool.network_fail:
            raise ConnectionError("connection reset by peer")
        return f"answer from {self.model_name}"


class StubProvider:
    """Owns which combinations are 'out of quota' and what was called."""

    def __init__(self):
        self.dead = set()
        self.calls = []
        self.network_fail = False

    def factory(self, key, model_name):
        return StubModel(key, model_name, self)

    def kill(self, *combos):
        self.dead.update(combos)

    def kill_all_keys_on(self, model_name, keys=KEYS):
        self.dead.update((k, model_name) for k in keys)


def build(keys=KEYS, models=(PRIMARY, FALLBACK)):
    provider = StubProvider()
    return GeminiKeyPool(list(keys), list(models), provider.factory), provider


def run(pool):
    return pool.execute(lambda model: model.generate_content("q"))


class TestFailover(unittest.TestCase):
    def test_exhausting_key_one_moves_to_key_two_on_the_same_model(self):
        pool, provider = build()
        provider.kill((KEYS[0], PRIMARY))

        self.assertEqual(run(pool), f"answer from {PRIMARY}")
        self.assertEqual(pool.active.key_index, 2)
        self.assertEqual(pool.active.model_name, PRIMARY, "must not jump models early")
        # Exactly one wasted call, on the dead key. No retry of it.
        self.assertEqual(provider.calls, [(KEYS[0], PRIMARY), (KEYS[1], PRIMARY)])

    def test_all_keys_spent_on_primary_falls_back_to_key_one_on_the_second_model(self):
        pool, provider = build()
        provider.kill_all_keys_on(PRIMARY)

        self.assertEqual(run(pool), f"answer from {FALLBACK}")
        self.assertEqual(pool.active.model_name, FALLBACK)
        self.assertEqual(pool.active.key_index, 1, "the fallback model starts again at key 1")
        # Every key tried once on the primary, in order, then key 1 again.
        self.assertEqual(
            provider.calls,
            [(k, PRIMARY) for k in KEYS] + [(KEYS[0], FALLBACK)],
        )

    def test_everything_spent_raises_all_providers_exhausted(self):
        pool, provider = build()
        provider.kill_all_keys_on(PRIMARY)
        provider.kill_all_keys_on(FALLBACK)

        with self.assertRaises(AllProvidersExhausted) as caught:
            run(pool)
        self.assertEqual(caught.exception.tried, 10)
        self.assertEqual(len(provider.calls), 10, "each combination tried exactly once")
        self.assertIsNone(pool.active)

    def test_all_providers_exhausted_is_not_a_rate_limit_error(self):
        """They mean different things and must not be caught interchangeably."""
        from ai.adapters.base import RateLimitError

        self.assertFalse(issubclass(AllProvidersExhausted, RateLimitError))

    def test_an_exhausted_combination_is_never_tried_again(self):
        pool, provider = build()
        provider.kill((KEYS[0], PRIMARY), (KEYS[1], PRIMARY))

        run(pool)
        provider.calls.clear()
        for _ in range(3):
            run(pool)

        self.assertEqual(
            provider.calls,
            [(KEYS[2], PRIMARY)] * 3,
            "later requests must go straight to the working combination",
        )

    def test_a_working_combination_is_sticky(self):
        """No rediscovering that keys 1 and 2 are empty on every request."""
        pool, provider = build()
        provider.kill((KEYS[0], PRIMARY), (KEYS[1], PRIMARY))
        run(pool)

        first_pass = len(provider.calls)
        run(pool)
        self.assertEqual(
            len(provider.calls) - first_pass, 1, "the second request should cost one call"
        )

    def test_a_network_error_does_not_burn_a_key(self):
        pool, provider = build()
        provider.network_fail = True

        with self.assertRaises(ConnectionError):
            run(pool)

        self.assertEqual(pool.status()["pools_exhausted"], 0, "a blip is not a spent quota")
        self.assertEqual(pool.active.key_index, 1)
        self.assertEqual(len(provider.calls), 1, "and it must not walk the whole pool")

    def test_a_malformed_response_does_not_burn_a_key(self):
        """Parsing happens after the call; a bad body says nothing about quota."""
        pool, _ = build()
        with self.assertRaises(ValueError):
            pool.execute(lambda model: (_ for _ in ()).throw(ValueError("not JSON")))
        self.assertEqual(pool.status()["pools_exhausted"], 0)

    def test_quota_wording_variants_all_count_as_exhausted(self):
        for message in (
            "429 Too Many Requests",
            "RESOURCE_EXHAUSTED",
            "Resource exhausted: check quota",
            "You exceeded your current quota",
            "rate limit reached",
        ):
            with self.subTest(message=message):
                pool, provider = build(keys=KEYS[:2], models=(PRIMARY,))
                calls = {"n": 0}

                def call(model, message=message):
                    calls["n"] += 1
                    if calls["n"] == 1:
                        raise QuotaError(message)
                    return "ok"

                self.assertEqual(pool.execute(call), "ok")
                self.assertEqual(pool.active.key_index, 2)


class AuthError(Exception):
    """Shaped like the SDK's 400 for a typo'd or revoked key."""

    def __init__(self, message='400 API key not valid. Please pass a valid API key. [reason: "API_KEY_INVALID"]'):
        super().__init__(message)


class TestInvalidKeysSkip(unittest.TestCase):
    """A bad key must not look like an outage.

    Failing over on quota but not on auth meant one typo in slot 1 failed
    every request while slots 2-5 sat unused. On a demo morning that is
    indistinguishable from everything being down, and the fix is a one-line
    edit nobody would think to make.
    """

    def test_invalid_key_one_falls_through_to_valid_key_two(self):
        pool, provider = build()
        bad = {KEYS[0]}

        def call(model):
            provider.calls.append((model.key, model.model_name))
            if model.key in bad:
                raise AuthError()
            return f"answer from {model.model_name}"

        self.assertEqual(pool.execute(call), f"answer from {PRIMARY}")
        self.assertEqual(pool.active.key_index, 2)
        self.assertEqual(pool.active.model_name, PRIMARY)

    def test_an_invalid_key_is_retired_on_every_model_at_once(self):
        """It is the KEY that is rejected, not the key/model pair.

        Retiring only the one combination would rediscover the same typo on
        the fallback model later, at the cost of another wasted call in front
        of an audience.
        """
        pool, provider = build()

        def call(model):
            provider.calls.append((model.key, model.model_name))
            if model.key == KEYS[0]:
                raise AuthError()
            return "ok"

        pool.execute(call)
        retired = [c for c in pool.combinations if c.key_index == 1]
        self.assertTrue(all(c.exhausted for c in retired), "both model slots must retire")
        self.assertTrue(all(c.state == "invalid" for c in retired))
        self.assertEqual(
            provider.calls,
            [(KEYS[0], PRIMARY), (KEYS[1], PRIMARY)],
            "exactly one wasted call on the bad key",
        )

    def test_invalid_and_exhausted_are_counted_separately(self):
        """A typo is fixed in app/.env; a quota is waited out. Different jobs."""
        pool, provider = build(keys=KEYS[:3], models=(PRIMARY,))

        def call(model):
            provider.calls.append((model.key, model.model_name))
            if model.key == KEYS[0]:
                raise AuthError()
            if model.key == KEYS[1]:
                raise QuotaError()
            return "ok"

        pool.execute(call)
        status = pool.status()
        self.assertEqual(status["pools_invalid"], 1)
        self.assertEqual(status["pools_exhausted"], 1)
        self.assertEqual(status["keys_invalid"], [1])

    def test_the_two_are_logged_differently(self):
        pool, provider = build(keys=KEYS[:3], models=(PRIMARY,))

        def call(model):
            if model.key == KEYS[0]:
                raise AuthError()
            if model.key == KEYS[1]:
                raise QuotaError()
            return "ok"

        with self.assertLogs("ai.adapters.keypool", level=logging.WARNING) as captured:
            pool.execute(call)
        blob = "\n".join(captured.output)
        self.assertIn("key 1 invalid, skipping", blob)
        self.assertIn("key 2 exhausted, switching", blob)
        for key in KEYS:
            self.assertNotIn(key, blob)

    def test_every_key_invalid_raises_rather_than_hanging(self):
        pool, _ = build()
        with self.assertRaises(AllProvidersExhausted):
            pool.execute(lambda model: (_ for _ in ()).throw(AuthError()))

    def test_auth_wording_variants(self):
        for message in (
            '400 API key not valid. [reason: "API_KEY_INVALID"]',
            "403 PERMISSION_DENIED: Generative Language API has not been used",
            "401 Unauthorized",
            "UNAUTHENTICATED: credentials missing",
        ):
            with self.subTest(message=message):
                pool, _ = build(keys=KEYS[:2], models=(PRIMARY,))
                seen = {"n": 0}

                def call(model, message=message):
                    seen["n"] += 1
                    if seen["n"] == 1:
                        raise AuthError(message)
                    return "ok"

                self.assertEqual(pool.execute(call), "ok")
                self.assertEqual(pool.active.key_index, 2)

    def test_a_network_error_still_does_not_burn_a_key(self):
        """The new auth branch must not have widened what counts as fatal."""
        pool, provider = build()
        provider.network_fail = True
        with self.assertRaises(ConnectionError):
            run(pool)
        self.assertEqual(pool.status()["pools_exhausted"], 0)
        self.assertEqual(pool.status()["pools_invalid"], 0)

    def test_numbers_that_merely_look_like_status_codes_are_not_auth_errors(self):
        """A session id containing 401 must not retire a working key."""
        pool, _ = build()
        with self.assertRaises(RuntimeError):
            pool.execute(
                lambda m: (_ for _ in ()).throw(RuntimeError("session mk-4013fe timed out"))
            )
        self.assertEqual(pool.status()["pools_invalid"], 0)


class TestPoolSize(unittest.TestCase):
    def test_two_of_five_keys_configured_is_a_two_key_pool(self):
        env = {
            "GEMINI_API_KEY_1": "a",
            "GEMINI_API_KEY_2": "",
            "GEMINI_API_KEY_3": "c",
            "GEMINI_API_KEY_4": None,
            "GEMINI_MODEL": PRIMARY,
        }
        keys = collect_keys(env)
        self.assertEqual(len(keys), 2, "blank and absent slots are skipped, not counted")
        pool, _ = build(keys=keys, models=(PRIMARY,))
        self.assertEqual(pool.status()["pools_total"], 2)
        self.assertEqual(pool.status()["keys_configured"], 2)

    def test_the_legacy_single_key_still_works(self):
        """Nothing may break before the numbered keys are pasted in."""
        env = {"GEMINI_API_KEY": "the-original-key", "GEMINI_MODEL": PRIMARY}
        self.assertEqual(collect_keys(env), ["the-original-key"])
        self.assertEqual(collect_models(env), [PRIMARY])

    def test_numbered_keys_take_precedence_over_the_legacy_one(self):
        env = {"GEMINI_API_KEY": "old", "GEMINI_API_KEY_1": "new", "GEMINI_MODEL": PRIMARY}
        self.assertEqual(collect_keys(env), ["new"])

    def test_a_duplicated_key_is_counted_once(self):
        """Two slots holding one key is one allowance, and must not look like two."""
        env = {"GEMINI_API_KEY_1": "same", "GEMINI_API_KEY_2": "same", "GEMINI_MODEL": PRIMARY}
        self.assertEqual(collect_keys(env), ["same"])

    def test_no_fallback_model_is_a_single_model_pool(self):
        env = {"GEMINI_API_KEY_1": "a", "GEMINI_MODEL": PRIMARY, "GEMINI_MODEL_FALLBACK": ""}
        self.assertEqual(collect_models(env), [PRIMARY])

    def test_five_keys_and_two_models_make_ten_pools(self):
        pool, _ = build()
        self.assertEqual(pool.status()["pools_total"], 10)

    def test_no_keys_at_all_raises_rather_than_pretending(self):
        pool = GeminiKeyPool([], [PRIMARY], lambda k, m: None)
        with self.assertRaises(AllProvidersExhausted):
            run(pool)


class TestNoKeyEverReachesTheLogs(unittest.TestCase):
    """This output goes to a terminal that will be on a projector."""

    def test_switching_logs_the_index_not_the_key(self):
        pool, provider = build()
        provider.kill_all_keys_on(PRIMARY)

        with self.assertLogs("ai.adapters.keypool", level=logging.WARNING) as captured:
            run(pool)

        blob = "\n".join(captured.output)
        for key in KEYS:
            self.assertNotIn(key, blob, "a key value reached the logs")
        self.assertIn("key 1 exhausted, switching to key 2", blob)
        self.assertIn("switching to the fallback model", blob)

    def test_status_carries_no_key_material(self):
        pool, provider = build()
        provider.kill((KEYS[0], PRIMARY))
        run(pool)

        blob = repr(pool.status())
        for key in KEYS:
            self.assertNotIn(key, blob)
        self.assertIn("key 1 of 5", blob)

    def test_a_failure_reason_is_scrubbed_of_anything_key_shaped(self):
        pool, provider = build(keys=KEYS[:2], models=(PRIMARY,))
        calls = {"n": 0}

        def call(model):
            calls["n"] += 1
            if calls["n"] == 1:
                raise QuotaError("429 quota exceeded (api_key=AIzaSyEXAMPLE12345)")
            return "ok"

        pool.execute(call)
        reason = pool.combinations[0].reason
        self.assertNotIn("AIzaSyEXAMPLE12345", reason)
        self.assertIn("<redacted>", reason)


class TestTheAppActuallyUsesThePool(unittest.TestCase):
    """The pool is worthless if the app builds its adapters around it.

    app/ai_bridge.py constructed the adapter with an explicit key and model,
    which pins it to that one pair and skips the failover entirely. Every unit
    test above still passed; a live call retired one combination and gave up.
    This asserts the wiring, not the logic.
    """

    def test_the_bridge_shares_the_process_pool(self):
        from app import ai_bridge
        from ai.adapters.base import MissingConfigError
        from ai.adapters.gemini import get_pool

        try:
            shared = get_pool()
        except MissingConfigError:
            self.skipTest("no Gemini key configured in this environment")

        ai_bridge._llm_singleton = None
        try:
            self.assertIs(
                ai_bridge._llm().pool,
                shared,
                "the bridge built its own single-combination pool and the "
                "failover would never run",
            )
        finally:
            ai_bridge._llm_singleton = None


if __name__ == "__main__":
    unittest.main()
