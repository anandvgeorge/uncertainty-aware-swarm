#!/usr/bin/env bash
# Build checks only: no simulator, desktop access, or development volumes.
set -euo pipefail

repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
log_dir=${1:-$(mktemp -d -t swarm-ci-build-XXXXXX)}
mkdir -p "$log_dir"
log_dir=$(cd -- "$log_dir" && pwd)
run_id="swarm-ci-build-$(date +%s)-$$"

cleanup() {
    docker rm -f "$run_id" >/dev/null 2>&1 || true
    if [[ -z ${SWARM_CI_IMAGE_PREFIX:-} ]]; then
        for service in builder autonomy gazebo; do
            docker image rm "$run_id-$service" >/dev/null 2>&1 || true
        done
    fi
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "Build logs: $log_dir"
for service in builder autonomy gazebo; do
    if [[ -n ${SWARM_CI_IMAGE_PREFIX:-} ]]; then
        # Fail on missing images rather than pulling an unrelated registry tag.
        docker image inspect "$SWARM_CI_IMAGE_PREFIX-$service:latest" \
            >"$log_dir/image-$service.log"
    else
        docker build --progress=plain \
        --file "$repo_root/docker/Dockerfile.$service" \
        --tag "$run_id-$service" "$repo_root" \
        2>&1 | tee "$log_dir/image-$service.log"
    fi
done
image_prefix=${SWARM_CI_IMAGE_PREFIX:-$run_id}

# A new container's writable layer holds build/install artifacts. Nothing is
# reused from the developer workspace, and --rm discards them on completion.
docker run --rm --name "$run_id" \
    --mount "type=bind,source=$repo_root/src,target=/workspace/ros2_ws/src,readonly" \
    --mount "type=bind,source=$repo_root/docker/build-workspace.sh,target=/ci/build-workspace.sh,readonly" \
    --mount "type=bind,source=$repo_root/scripts/ci-verify-install.sh,target=/ci/verify-install.sh,readonly" \
    --mount "type=bind,source=$log_dir,target=/workspace/ros2_ws/log" \
    "$image_prefix-builder:latest" bash -c \
    'bash /ci/build-workspace.sh --event-handlers console_direct+ && bash /ci/verify-install.sh' \
    2>&1 | tee "$log_dir/workspace.log"
