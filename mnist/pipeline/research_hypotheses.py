"""Phase-1 research hypothesis log.

Each loop prepends one dict to `RESEARCH_HYPOTHESES` (newest first).
"""

from __future__ import annotations

RESEARCH_HYPOTHESES: list[dict] = [
    {
        "hypothesis_id": "model_architecture-h3",
        "theme": "block_kwta_activation_cost",
        "hypothesis": (
            "Each MnistCNN ResNet18 forward applies KWTA(k=10) 17 times per sub-network "
            "(stem conv plus two KWTA calls in every BasicBlock across [2,2,2,2] stages "
            "in model.py); kWTA.forward runs torch.topk over the full activation tensor "
            "(mnist/pipeline/kwta.py). With train.py defaults num_sub_networks=3, ensemble "
            "inference executes ~51 topk passes per sample via the Python loop in "
            "train_optuna.py EnsembleMnistCNN.forward. Early maps are largest (layer1: "
            "64x28x28 = 50,176 elements), so KWTA dominates conv FLOPs on CPU and pushes "
            "latency_ms past baseline.json (<= 13.0). Replacing KWTA with ReLU in layer3 "
            "and layer4 blocks while keeping KWTA in stem/layer1/layer2 should preserve "
            "sparsity where it matters and recover enough ms/sample to hold accuracy >= "
            "0.985 under the latency gate without shrinking the 3-member ensemble."
        ),
        "planned_change": (
            "In mnist/pipeline/model.py: parameterize BasicBlock/ResNet with per-stage "
            "activation (KWTA vs ReLU); default layer3/layer4 blocks to ReLU, keep KWTA "
            "in stem/layer1/layer2; retrain EnsembleMnistCNN (num_sub_networks=3) and "
            "re-measure latency_ms via mnist/pipeline/train.py."
        ),
        "run_id": "run_ffbe92342ffe",
        "timestamp": "2026-05-26T00:21:08.103783+00:00",
    },
    {
        "hypothesis_id": "model_architecture-h2",
        "theme": "shared_trunk_ensemble",
        "hypothesis": (
            "EnsembleMnistCNN (train.py defaults: num_sub_networks=3, kwta_k=1) runs "
            "three full independent ResNet18 forwards per sample via "
            "torch.stack([model(x) for model in self.models]) in train_optuna.py, so "
            "inference latency scales ~linearly with sub-network count while only the "
            "top-1 logit vote is used. mnist/baseline.json requires latency_ms <= 13.0 "
            "at accuracy >= 0.985. A single shared trunk through ResNet layer3 with "
            "three lightweight layer4+linear heads and the same ensemble top-k at logits "
            "should preserve kWTA voting diversity at roughly one shared-backbone pass "
            "instead of three full copies."
        ),
        "planned_change": (
            "In mnist/pipeline/model.py: add SharedTrunkEnsembleMnistCNN with one "
            "ResNet18 trunk through layer3 and three head branches; refactor "
            "EnsembleMnistCNN forward to use it (or delegate); align train.py and "
            "mnist/eval/run_eval.py checkpoint wiring; re-measure latency_ms."
        ),
        "run_id": "run_b8a45c0f3c54",
        "timestamp": "2026-05-26T00:19:13.851679+00:00",
    },
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
