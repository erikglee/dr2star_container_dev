#!/usr/bin/env python3
"""BIDS-style wrapper to run dr2star-core with the fmriprep workflow."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

from . import utilities
from .my_parser import get_parser


def build_cmd_template(
    bold_path: Path,
    censor_output_path: Path,
    mask_path: Path,
    output_path: Path,
    args,
) -> list[str]:
    """Build a minimal tat2 command for a single run."""
    cmd = [
        "tat2",
        str(bold_path),
        "-censor_rel",
        str(censor_output_path),
        "-mask",
        str(mask_path),
        "-output",
        str(output_path),
    ]
    if args.scale is not None:
        cmd.extend(["-scale", str(args.scale)])
    if args.no_voxscale:
        cmd.append("-no_voxscale")
    if args.inverse:
        cmd.append("-inverse")
    if args.time_norm == "mean":
        cmd.append("-mean_time")
    elif args.time_norm == "median":
        cmd.append("-median_time")

    if args.volume_norm == "mean":
        cmd.append("-mean_vol")
    elif args.volume_norm == "median":
        cmd.append("-median_vol")
    elif args.volume_norm == "none":
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
    return cmd


def _normalize_labels(labels: list[str], prefix: str) -> list[str]:
    return [label.removeprefix(prefix) for label in labels]


def _discover_subjects(input_dir: Path, requested: list[str]) -> list[str]:
    if requested:
        return requested
    subjects = sorted(
        path.name.removeprefix("sub-")
        for path in input_dir.glob("sub-*")
        if path.is_dir()
    )
    if not subjects:
        raise FileNotFoundError(f"No subject directories found under {input_dir}")
    return subjects


def _discover_sessions(subject_dir: Path, requested: list[str]) -> list[str | None]:
    sessions = sorted(
        path.name.removeprefix("ses-")
        for path in subject_dir.glob("ses-*")
        if path.is_dir()
    )
    if sessions:
        if requested:
            sessions = [session for session in sessions if session in requested]
            if not sessions:
                raise FileNotFoundError(
                    f"No requested sessions found under {subject_dir}"
                )
        return sessions
    if requested:
        raise FileNotFoundError(
            f"Session labels provided but no ses-* directories found under {subject_dir}"
        )
    return [None]


def _replace_confounds_suffix(filename: str, suffix: str) -> str:
    if filename.endswith("_desc-confounds_timeseries.tsv"):
        return filename.replace("_desc-confounds_timeseries.tsv", suffix)
    if filename.endswith("_desc-confounds_regressors.tsv"):
        return filename.replace("_desc-confounds_regressors.tsv", suffix)
    raise NameError(f"Unexpected confound file name format: {filename}")


def main(argv: list[str] | None = None) -> int:
    parser = get_parser()
    args = parser.parse_args(argv)

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    participant_labels = _normalize_labels(args.participant_label or [], "sub-")
    ses_labels = _normalize_labels(args.ses_label or [], "ses-")

    if participant_labels:
        print(f"Participants: {', '.join(participant_labels)}")
    else:
        print("Participants: all")
    if ses_labels:
        print(f"Sessions: {', '.join(ses_labels)}")
    else:
        print("Sessions: all")

    env = os.environ.copy()
    env.setdefault(
        "FMRIPREP_TASK_PATTERN",
        "*_task-*space-MNI152NLin6Asym_res-2*desc-preproc_bold.nii.gz",
    )
    if args.fd_thres is not None:
        env["FD_THRES"] = str(args.fd_thres)

    subjects = _discover_subjects(input_dir, participant_labels)
    #Iterate through all possible subjects
    for temp_subject in subjects:
        subject_dir = input_dir / f"sub-{temp_subject}"
        sessions = _discover_sessions(subject_dir, ses_labels)
        #Iterate through all possible sessions
        for temp_session in sessions:
            if temp_session:
                func_directory = subject_dir / f"ses-{temp_session}" / "func"
                confound_patterns = [
                    f"sub-{temp_subject}_ses-{temp_session}_*desc-confounds_timeseries.tsv",
                    f"sub-{temp_subject}_ses-{temp_session}_*desc-confounds_regressors.tsv",
                ]
                output_anat_dir = (
                    output_dir
                    / f"sub-{temp_subject}"
                    / f"ses-{temp_session}"
                    / "anat"
                )
            else:
                func_directory = subject_dir / "func"
                confound_patterns = [
                    f"sub-{temp_subject}_*desc-confounds_timeseries.tsv",
                    f"sub-{temp_subject}_*desc-confounds_regressors.tsv",
                ]
                output_anat_dir = output_dir / f"sub-{temp_subject}" / "anat"

            #Find all confound files for this subject/session. There
            #will be one confound file per fMRI acquisition.
            confound_files: list[Path] = []
            for pattern in confound_patterns:
                confound_files.extend(func_directory.glob(pattern))
            confound_files = sorted({path for path in confound_files})

            #If the user specified specific task labels, be sure to only keep those
            #confound files that match the requested tasks.
            if args.task_id:
                task_ids = [task.removeprefix("task-") for task in args.task_id]
                confound_files = [
                    path
                    for path in confound_files
                    if any(f"_task-{task}_" in path.name for task in task_ids)
                ]

            output_anat_dir.mkdir(parents=True, exist_ok=True)

            #For every confound file, try to run the dr2star pipeline.
            for confound_file in confound_files:

                #Populate the corresponding output censor file name.
                confound_name = confound_file.name
                censor_name = _replace_confounds_suffix(
                    confound_name,
                    "_desc-dr2star_censor.1D",
                )
                censor_output_path = output_anat_dir / censor_name
                
                #Create the censor file from the confounds and the given thresholds.
                utilities.confounds_to_censor_file(
                    confound_file,
                    str(censor_output_path),
                    fd_thres=args.fd_thres,
                    dvars_thresh=args.dvars_thresh,
                )

                space_token = args.space.replace(":", "_")
                bold_name = _replace_confounds_suffix(
                    confound_name,
                    f"_space-{space_token}_desc-preproc_bold.nii.gz",
                )
                bold_path = func_directory / bold_name
                if not bold_path.exists():
                    raise FileNotFoundError(
                        f"Missing preproc bold file for space '{args.space}': {bold_path}"
                    )

                if args.mask_input is None:
                    mask_name = _replace_confounds_suffix(
                        confound_name,
                        f"_space-{space_token}_desc-brain_mask.nii.gz",
                    )
                    mask_path = func_directory / mask_name
                else:
                    mask_input = Path(args.mask_input)
                    if mask_input.is_file():
                        mask_path = mask_input
                    elif mask_input.is_dir():
                        raise NotImplementedError(
                            "Mask derivatives directory support is not implemented yet."
                        )
                    else:
                        raise FileNotFoundError(
                            f"--mask-input does not exist: {args.mask_input}"
                        )

                if not bold_name.endswith("_desc-preproc_bold.nii.gz"):
                    raise NameError(f"Unexpected bold file name format: {bold_name}")
                output_name = bold_name.replace(
                    "_desc-preproc_bold.nii.gz",
                    "_desc-dr2star_dr2starmap.nii.gz",
                )
                output_path = output_anat_dir / output_name

                cmd_template = build_cmd_template(
                    bold_path,
                    censor_output_path,
                    mask_path,
                    output_path,
                    args,
                )
                try:
                    result = subprocess.run(cmd_template, check=False, env=env)
                except FileNotFoundError:
                    parser.error("'tat2' not found on PATH. Ensure it is installed or in PATH.")

                if result.returncode != 0:
                    return result.returncode

                log_json = Path(str(output_path).replace(".nii.gz", ".log.json"))
                if log_json.exists():
                    sidecar_json = Path(str(output_path).replace(".nii.gz", ".json"))
                    log_json.replace(sidecar_json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
