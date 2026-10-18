import sys
import json
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'pipeline'))
from extension_audit import context_settings, token_count
from extension_prepare import additional_models, replace_once
from extension_batch import freeze_driver_metadata


class ExtensionTests(unittest.TestCase):
    def test_effective_context_metadata_freezes_before_inference(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary)
            protocol = dict(test_released=False, input_pins=[], max_model_len=32768,
                            models=[dict(max_model_len=40960, kv_cache_memory_bytes=7 * 1024**3)])
            (out / 'protocol.json').write_text(json.dumps(protocol))
            freeze_driver_metadata(out)
            frozen = json.loads((out / 'protocol.json').read_text())
            self.assertEqual(frozen['max_model_len'], 40960)
            self.assertEqual((out / 'protocol.dev.json').read_bytes(), (out / 'protocol.json').read_bytes())
            (out / 'dev.fixture.results.jsonl').write_text('{}\n')
            (out / 'protocol.json').write_text(json.dumps(protocol))
            with self.assertRaisesRegex(ValueError, 'inference started'):
                freeze_driver_metadata(out)

    def test_all_additional_models_load_separate_frozen_weight_manifests(self):
        models = additional_models()
        self.assertEqual(len(models), 5)
        for model in models:
            self.assertTrue(model['pins'])
            self.assertTrue(any(row['path'].endswith('.safetensors') for row in model['pins']))

    def test_context_includes_output_and_never_exceeds_native_limit(self):
        config = dict(max_position_embeddings=40960, hidden_size=4096, num_attention_heads=32,
                      num_key_value_heads=8, num_hidden_layers=40)
        settings = context_settings(config, 33000)
        self.assertEqual(settings['max_model_len'], 33792)
        self.assertGreaterEqual(settings['kv_cache_memory_bytes'], 33792 * 2 * 2 * 40 * 8 * 128)
        with self.assertRaisesRegex(ValueError, 'native context'):
            context_settings(config, 40960)

    def test_chat_options_are_applied_to_audited_tokens(self):
        class Tokenizer:
            def apply_chat_template(self, messages, **kwargs):
                assert kwargs['enable_thinking'] is False
                assert kwargs['add_generation_prompt'] is True
                return {'input_ids': [1, 2, 3]}
        self.assertEqual(token_count(Tokenizer(), [], dict(enable_thinking=False)), 3)

    def test_adapter_refuses_missing_or_ambiguous_source(self):
        self.assertEqual(replace_once('abc', 'b', 'd'), 'adc')
        for text in ('abc', 'bbbb'):
            with self.assertRaises(ValueError):
                replace_once(text, 'bb', 'x')


if __name__ == '__main__':
    unittest.main()
