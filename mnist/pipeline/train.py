#!/usr/bin/env python3
"""Train MNIST CNN and write metrics for the eval gate."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, transforms

from model import MnistCNN


def _load_baseline(mnist_root: Path) -> dict:
    return json.loads((mnist_root / "baseline.json").read_text(encoding="utf-8"))


def _accuracy(model: nn.Module, loader: DataLoader, device: torch.device) -> float:
    model.eval()
    correct = 0
    total = 0
    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            labels = labels.to(device)
            preds = model(images).argmax(dim=1)
            correct += (preds == labels).sum().item()
            total += labels.size(0)
    return correct / max(total, 1)


def _latency_ms(model: nn.Module, loader: DataLoader, device: torch.device, samples: int = 256) -> float:
    model.eval()
    seen = 0
    start = time.perf_counter()
    with torch.no_grad():
        for images, _ in loader:
            images = images.to(device)
            _ = model(images)
            seen += images.size(0)
            if seen >= samples:
                break
    elapsed = time.perf_counter() - start
    return (elapsed / max(seen, 1)) * 1000.0


def main() -> None:
    parser = argparse.ArgumentParser(description="Train MNIST CNN.")
    parser.add_argument("--mnist-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--epochs", type=int, default=3)
    parser.add_argument("--batch-size", type=int, default=128)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--quick", action="store_true", help="Use a small train subset for fast smoke runs.")
    parser.add_argument("--device", default="cpu")
    parser.add_argument("--output", type=Path, default=None, help="Metrics JSON path.")
    parser.add_argument("--checkpoint", type=Path, default=None, help="Model checkpoint path.")
    args = parser.parse_args()

    mnist_root = args.mnist_root.resolve()
    baseline = _load_baseline(mnist_root)
    device = torch.device(args.device)

    transform = transforms.Compose([transforms.ToTensor(), transforms.Normalize((0.1307,), (0.3081,))])
    data_dir = mnist_root / "data"
    train_set = datasets.MNIST(str(data_dir), train=True, download=True, transform=transform)
    test_set = datasets.MNIST(str(data_dir), train=False, download=True, transform=transform)
    if args.quick:
        train_set = Subset(train_set, range(2000))
        test_set = Subset(test_set, range(1000))

    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True, num_workers=0)
    test_loader = DataLoader(test_set, batch_size=args.batch_size, shuffle=False, num_workers=0)

    model = MnistCNN().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss()

    for _ in range(args.epochs):
        model.train()
        for images, labels in train_loader:
            images = images.to(device)
            labels = labels.to(device)
            optimizer.zero_grad()
            loss = criterion(model(images), labels)
            loss.backward()
            optimizer.step()

    accuracy = _accuracy(model, test_loader, device)
    latency_ms = _latency_ms(model, test_loader, device)

    ckpt_dir = mnist_root / "pipeline" / "checkpoints"
    ckpt_dir.mkdir(parents=True, exist_ok=True)
    checkpoint_path = args.checkpoint or (ckpt_dir / "mnist_cnn.pt")
    torch.save({"model_state_dict": model.state_dict(), "accuracy": accuracy}, checkpoint_path)

    metrics = {
        "accuracy": round(accuracy, 6),
        "latency_ms": round(latency_ms, 4),
        "epochs": args.epochs,
        "baseline_accuracy": baseline["accuracy"],
        "baseline_latency_ms": baseline["latency_ms"],
        "checkpoint": str(checkpoint_path.relative_to(mnist_root)),
        "device": str(device),
        "quick_mode": args.quick,
    }
    out = args.output or (mnist_root / "pipeline" / "last_train_metrics.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metrics))


if __name__ == "__main__":
    main()
