# Platform Overview

The platform is built in clear layers.

The bootstrap repository owns cloud foundation resources such as Terraform, network, and low-cost Alibaba base infrastructure.

The gitops environments repository owns desired deployment state and should stay separate from Terraform-managed cloud resources.

The ai runtime repository owns FastAPI request handling, model client boundaries, session state, and future retrieval orchestration.
