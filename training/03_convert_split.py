# Training Script: Sequence-Grouped Dataset Split & Label Converter
# Group images by capture sequence prefix to prevent train/test leakage across adjacent video frames.

import argparse
import os
import random
from collections import defaultdict


def sequence_grouped_split(image_dir: str, train_ratio: float = 0.70, val_ratio: float = 0.15, test_ratio: float = 0.15):
    """
    Groups images by sequence (common prefix before timestamp/index) before splitting.
    """
    images = [f for f in os.listdir(image_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    sequences = defaultdict(list)

    for img in images:
        # Group by sequence key, e.g., 'seq1_001.jpg' -> 'seq1'
        seq_key = img.split('_')[0] if '_' in img else img[:4]
        sequences[seq_key].append(img)

    seq_keys = list(sequences.keys())
    random.seed(42)
    random.shuffle(seq_keys)

    n_total = len(seq_keys)
    n_train = int(n_total * train_ratio)
    n_val = int(n_total * val_ratio)

    train_seqs = set(seq_keys[:n_train])
    val_seqs = set(seq_keys[n_train:n_train + n_val])
    test_seqs = set(seq_keys[n_train + n_val:])

    split_counts = {"train": 0, "val": 0, "test": 0}
    for k, files in sequences.items():
        if k in train_seqs:
            split_counts["train"] += len(files)
        elif k in val_seqs:
            split_counts["val"] += len(files)
        else:
            split_counts["test"] += len(files)

    print(f"Sequence split complete across {n_total} sequences:")
    print(f"Train: {split_counts['train']} frames ({len(train_seqs)} sequences)")
    print(f"Val:   {split_counts['val']} frames ({len(val_seqs)} sequences)")
    print(f"Test:  {split_counts['test']} frames ({len(test_seqs)} sequences)")
    return split_counts


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sequence-grouped split converter")
    parser.add_argument("--image_dir", type=str, default="data/raw/images", help="Path to raw image directory")
    args = parser.parse_args()
    if os.path.exists(args.image_dir):
        sequence_grouped_split(args.image_dir)
    else:
        print(f"Directory {args.image_dir} not found; run with valid dataset path.")
