#!/usr/bin/env python3
"""BIDS-style wrapper to run dr2star-core with the fmriprep workflow."""

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
        "dr2star-core",
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

    if args.scale is not None:
        cmd.extend(["-scale", str(args.scale)])
    if args.no_voxscale:
        cmd.append("-no_voxscale")
    if args.inverse:
        cmd.append("-inverse")
    if args.mean_time:
        cmd.append("-mean_time")
    if args.median_time:
        cmd.append("-median_time")
    if args.mean_vol:
        cmd.append("-mean_vol")
    if args.median_vol:
        cmd.append("-median_vol")
    if args.no_vol:
        cmd.append("-no_vol")
    if args.maxvols is not None:
        cmd.extend(["-maxvols", str(args.maxvols)])
    if args.maxvolstotal is not None:
        cmd.extend(["-maxvolstotal", str(args.maxvolstotal)])
    if args.sample_method:
        cmd.extend(["-sample_method", args.sample_method])
    if args.tmp_dir:
        cmd.extend(["-tmp", args.tmp_dir])
    if args.noclean:
        cmd.append("-noclean")
    if args.verbose:
        cmd.append("-verbose")

    env = os.environ.copy()
    env.setdefault(
        "FMRIPREP_TASK_PATTERN",
        "*_task-*space-MNI152NLin6Asym_res-2*desc-preproc_bold.nii.gz",
    )
    if args.fd_thres is not None:
        env["FD_THRES"] = str(args.fd_thres)

    try:
        result = subprocess.run(cmd, check=False, env=env)
    except FileNotFoundError:
        parser.error("'dr2star-core' not found on PATH. Ensure the script is installed or in PATH.")

    if result.returncode != 0:
        return result.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
