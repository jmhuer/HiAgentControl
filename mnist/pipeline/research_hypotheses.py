"""Structured hypothesis log for phase-1 research loops."""

from __future__ import annotations

HYPOTHESES: list[dict[str, str]] = [
    {
        "hypothesis_id": "model_architecture-h3",
        "theme": "width-adaptive-kwta",
        "hypothesis": "BasicBlock and the ResNet stem in model.py hard-code KWTA(k=10) while planes scale 64→512, so active fraction swings from 15.6% (64 ch) to 1.95% (512 ch)—an 8× sparsity mismatch that over-prunes deep features without saving latency because torch.topk cost grows with channel width. Using k=max(8, planes//8) per KWTA site holds ~12.5% density at every depth, keeps the same 17 (or h2-reduced) top-k call count, and should remain under the 13 ms latency gate.",
        "planned_change": "Mark width-adaptive k (planes//8) as the next KWTA hyperparameter experiment before editing BasicBlock/ResNet __init__ wiring.",
        "run_id": "run_654baef80b2d",
        "timestamp": "2026-05-26T00:04:15.978802+00:00"
    },
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

