FROM debian:13-slim

# ~10Mb of AFNI tools.  latest pulled 20260102, created 2025-12-18
COPY --from=docker.io/afni/afni_make_build@sha256:5e0d8733ed277ea58b4a527e88bc10f62572ee63308d97a5e5e340d4423b3804 \
  /opt/afni/install/libmri.so \
  /opt/afni/install/libf2c.so \
  /opt/afni/install/3dBrickStat \
  /opt/afni/install/3dcalc \
  /opt/afni/install/3dinfo \
  /opt/afni/install/3dNotes \
  /opt/afni/install/3dROIstats \
  /opt/afni/install/3dTcat \
  /opt/afni/install/3dTstat \
  /usr/bin/

# depends read from 'ldd': libz libexpat
RUN apt-get update -qq && \
  apt-get install -qy parallel libexpat1 zlib1g python3 && \
  rm -rf /var/lib/apt/lists/* 


COPY dr2star-core /usr/bin/
COPY dr2star/run.py /usr/bin/dr2star
COPY my_parser.py /usr/bin/
RUN chmod +x /usr/bin/dr2star-core /usr/bin/dr2star
ENTRYPOINT ["/usr/bin/dr2star"]
