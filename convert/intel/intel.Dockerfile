FROM openvino/ubuntu20_dev:2022.3.0
# ------------------------------------------------------------------
# Close noninteractive
ENV DEBIAN_FRONTEND noninteractive

# ------------------------------------------------------------------
USER root
WORKDIR /workspace

# ------------------------------------------------------------------
# Install intel_requirements.sh
COPY ./intel /workspace/convert/intel

RUN chmod +x /workspace/convert/intel/intel_requirements.sh \
&& /workspace/convert/intel/intel_requirements.sh

# ------------------------------------------------------------------
# Define Entrypoint
ENTRYPOINT [ "/bin/bash", "-c" ]