#!/usr/bin/env python3
import pandas as pd
import numpy as np


def confounds_to_censor_file(
    confounds_tsv: str,
    censor_output_path: str,
    fd_thres: float = 0.3,
    dvars_thresh: float | None = None,
) -> np.ndarray:
    """Generate a censor file from fmriprep confounds.

    Parameters
    ----------
    confounds_tsv : str
        Path to fmriprep confounds TSV file.
    censor_output_path : str
        Path to write the censor file (one 0/1 per row).
    fd_thres : float, optional
        Framewise displacement threshold for censoring, by default 0.3.
    dvars_thresh : float | None, optional
        DVARS threshold for censoring, by default None (not used).

    """
    confounds = pd.read_csv(confounds_tsv, sep="\t")

    fd = confounds.get("framewise_displacement")
    if fd is None:
        raise ValueError("Framewise displacement column not found in confounds.")

    censor = np.ones(len(confounds), dtype=int)
    censor[fd > fd_thres] = 0

    if dvars_thresh is not None:
        dvars = confounds.get("dvars")
        if dvars is None:
            raise ValueError("DVARS column not found in confounds.")
        censor[dvars > dvars_thresh] = 0

    # Save the censor file that can be used with AFNI commands
    np.savetxt(censor_output_path, censor, fmt="%d")

    return
