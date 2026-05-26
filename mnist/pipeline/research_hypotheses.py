"""Structured hypothesis log for phase-1 research loops."""

from __future__ import annotations

HYPOTHESES: list[dict[str, str]] = [
    {
        "hypothesis_id": "model_architecture-h2",
        "theme": "staged-kwta-latency",
        "hypothesis": "ResNet18 in model.py applies KWTA(k=10) at 17 points (stem plus two per BasicBlock) with fixed k regardless of channel width (64→512). For 28×28 MNIST, retaining KWTA only in stages 1–2 and swapping deeper KWTA for ReLU removes ~8 top-k ops on high-channel 7×7/3×3 maps, preserving the 13 ms latency budget while keeping early activation sparsity that h1 targets.",
        "planned_change": "Mark staged KWTA (layers 1–2 only) as the next architecture experiment candidate before editing BasicBlock/ResNet wiring.",
        "run_id": "run_4499a2ecb2aa",
        "timestamp": "2026-05-26T00:01:37.571258+00:00"
    },
    {
        "hypothesis_id": "model_architecture-h1",
        "theme": "sparsity-regularization",
        "hypothesis": "Increasing structured sparsity pressure can improve robustness without harming quick-test correctness.",
        "planned_change": "Track sparse activation marker for future model-architecture tuning.",
        "run_id": "run_59ee70483de8",
        "timestamp": "2026-05-25T23:02:55.906343+00:00"
    },
]

