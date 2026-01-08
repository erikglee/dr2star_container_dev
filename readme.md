# dR2*
## Usage

With a container
```
docker run \
  -v /path/to/fmriprep:/fmriprep \
  TODO/dR2star /fmriprep
```

As a script
```
# run only once (per compute environment)
git clone https://github.com/TODO/dR2star ~/dR2star

# setup when on cluster/hpc
module load afni

# actually run
~/dR2star/dR2s /path/to/fmriprep
```

## Output

 * `tat2star.nii.gz` - 3D nifti image with `3dNotes` history.
 * `tat2star.log.json` - pipeline provenance

## Developing
See tests in `t/`. Run with `make check`

## Provenance
Extracted from [lncdtools](https://github.com/lncd/lncdtools) on 2026-01-08.
```
git clone --branch tat2-fmriprep --single-branch lncdtools dR2star
find -iname '*tat2*' -not -ipath '*.git/*' |
  sed 's:^./:--path :'|
  xargs uv tool run git-filter-repo --force \
    --path Makefile \
    --path .github/workflows/ci.yml \
```
