#!/usr/bin/env python3
"""BIDS-style wrapper to run tat2 with the fmriprep workflow."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from my_parser import get_parser


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    cmd = [
        "tat2",
        "-fmriprep",
        str(input_dir),
        "--fmriprep-output",
        str(output_dir),
    ]

    participant_labels = args.participant_label or []
    ses_labels = args.ses_label or []

    if participant_labels:
        print(f"Participants: {', '.join(participant_labels)}")
    else:
        print("Participants: all")
    if ses_labels:
        print(f"Sessions: {', '.join(ses_labels)}")
    else:
        print("Sessions: all")

    for label in participant_labels:
        cmd.extend(["--participant-label", label])
    for label in ses_labels:
        cmd.extend(["--ses-label", label])

    env = os.environ.copy()
    env.setdefault(
        "FMRIPREP_TASK_PATTERN",
        "*_task-*space-MNI152NLin6Asym_res-2*desc-preproc_bold.nii.gz",
    )

    try:
        result = subprocess.run(cmd, check=False, env=env)
    except FileNotFoundError:
        parser.error("'tat2' not found on PATH. Ensure the script is installed or in PATH.")

    if result.returncode != 0:
        return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

