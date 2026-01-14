#!/usr/bin/env python3
"""Argument parsing for the dr2star wrapper."""

from __future__ import annotations

import argparse
import textwrap


def get_parser() -> argparse.ArgumentParser:
    description = """
    dr2star wrapper for tat2 fmriprep runs.

    This interface mirrors a BIDS App-style CLI with three positional
    arguments: input, output, and analysis level. Only the participant
    analysis level is supported.
    """

    epilog = """
    Examples
    --------
    Process all participants and sessions:
      run.py /data/derivatives/fmriprep /data/derivatives/dr2star participant

    Process a single participant:
      run.py /data/derivatives/fmriprep /data/derivatives/dr2star participant \
        --participant-label 01

    Process a single participant/session:
      run.py /data/derivatives/fmriprep /data/derivatives/dr2star participant \
        --participant-label 01 --ses-label 02
    """

    parser = argparse.ArgumentParser(
        prog="run.py",
        description=textwrap.dedent(description).strip(),
        epilog=textwrap.dedent(epilog).strip(),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "input_dir",
        metavar="INPUT_DIR",
        help=(
            "Path to fmriprep derivatives (input directory). "
            "This is passed to tat2 using -fmriprep."
        ),
    )
    parser.add_argument(
        "output_dir",
        metavar="OUTPUT_DIR",
        help=(
            "Root output directory. Outputs are written under "
            "OUTPUT_DIR/sub-<label>/ses-<label>/anat/."
        ),
    )
    parser.add_argument(
        "analysis_level",
        metavar="ANALYSIS_LEVEL",
        choices=["participant"],
        help="Processing level to run. Only 'participant' is supported.",
    )

    parser.add_argument(
        "--participant-label",
        dest="participant_label",
        metavar="LABEL",
        nargs="+",
        help=(
            "Optional participant label(s) (with or without 'sub-'). "
            "Provide one or more labels separated by spaces. "
            "Example: '01' or 'sub-01'."
        ),
    )
    parser.add_argument(
        "--ses-label",
        dest="ses_label",
        metavar="LABEL",
        nargs="+",
        help=(
            "Optional session label(s) (with or without 'ses-'). "
            "Provide one or more labels separated by spaces. "
            "Example: '01' or 'ses-01'."
        ),
    )

    return parser
