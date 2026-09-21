import unittest
from pathlib import Path
from types import SimpleNamespace

from roleweaver import __version__
from roleweaver.ai import (
    AIRequest,
    AIRequestPurpose,
    AIResult,
    OpenAICompatibleProvider,
    coerce_ai_result,
)


class AIContractTests(unittest.TestCase):
    def test_package_version_matches_release_version(self):
        version_file = Path(__file__).resolve().parents[1] / "VERSION"
        self.assertEqual(__version__, version_file.read_text(encoding="utf-8").strip())

    def test_legacy_text_is_normalized_without_inventing_usage(self):
        result = coerce_ai_result(
            "  hello  ",
            provider="Custom",
            model="example",
            purpose=AIRequestPurpose.TRANSLATION,
            duration_seconds=0.25,
        )
        self.assertIsInstance(result, AIResult)
        self.assertEqual(result.text, "hello")
        self.assertEqual(result.purpose, AIRequestPurpose.TRANSLATION)
        self.assertFalse(result.usage.available)

    def test_openai_response_is_returned_as_structured_result(self):
        response = SimpleNamespace(
            id="request-123",
            output_text="A measured reply.",
            usage=SimpleNamespace(input_tokens=17, output_tokens=4, total_tokens=21),
        )
        provider = OpenAICompatibleProvider.__new__(OpenAICompatibleProvider)
        provider.model = "test-model"
        provider.use_chat_completions = False
        provider.client = SimpleNamespace(
            responses=SimpleNamespace(create=lambda **kwargs: response)
        )

        result = provider.generate(
            AIRequest(
                instructions="instructions",
                prompt="prompt",
                purpose=AIRequestPurpose.SUMMARY,
            )
        )

        self.assertEqual(result.text, "A measured reply.")
        self.assertEqual(result.provider, "OpenAI")
        self.assertEqual(result.model, "test-model")
        self.assertEqual(result.purpose, AIRequestPurpose.SUMMARY)
        self.assertEqual(result.usage.input_tokens, 17)
        self.assertEqual(result.usage.output_tokens, 4)
        self.assertEqual(result.usage.total_tokens, 21)
        self.assertEqual(result.usage.source, "provider")
        self.assertEqual(result.provider_request_id, "request-123")

    def test_provider_zero_token_counts_are_not_treated_as_missing(self):
        response = SimpleNamespace(
            id="request-empty",
            output_text="",
            usage=SimpleNamespace(input_tokens=3, output_tokens=0, total_tokens=3),
        )
        provider = OpenAICompatibleProvider.__new__(OpenAICompatibleProvider)
        provider.model = "test-model"
        provider.use_chat_completions = False
        provider.client = SimpleNamespace(
            responses=SimpleNamespace(create=lambda **kwargs: response)
        )

        result = provider.generate("instructions", "prompt")

        self.assertEqual(result.usage.output_tokens, 0)
        self.assertTrue(result.usage.available)


if __name__ == "__main__":
    unittest.main()
