"""Phase-1 research hypothesis log.

Each loop prepends one dict to `RESEARCH_HYPOTHESES` (newest first).
"""

from __future__ import annotations

RESEARCH_HYPOTHESES: list[dict] = [
    {
        "hypothesis_id": "model_architecture-h1",
        "theme": "ensemble_inference_cost",
        "hypothesis": (
            "EnsembleMnistCNN (train.py/eval defaults: num_sub_networks=3, kwta_k=1) runs "
            "three sequential ResNet18 forwards per batch item; each MnistCNN uses a full "
            "4-stage ResNet ([2,2,2,2] blocks, 512-channel layer4, KWTA k=10 in every "
            "BasicBlock) on 28x28 MNIST. That stack is the dominant latency driver versus "
            "baseline.json (latency_ms <= 13.0, accuracy >= 0.985). A MNIST-sized single "
            "backbone (two residual stages, <=128 channels, ReLU activations) should cut "
            "ms/sample enough to stay under the gate, with headroom to re-add a 2-member "
            "KWTA ensemble if accuracy drops."
        ),
        "planned_change": (
            "In mnist/pipeline/model.py: add a shallow MnistResNet variant; set "
            "EnsembleMnistCNN default num_sub_networks=1 (or 2) and align train/eval "
            "checkpoint metadata; re-measure latency_ms via mnist/eval/run_eval.py."
        ),
        "run_id": "run_4e5ee3a7c42b",
        "timestamp": "2026-05-26T00:16:57.014292+00:00",
    },
]
