#!/usr/bin/env bash
# Run the baseline with software rendering and disposable Compose resources.
set -euo pipefail
repo_root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
log_dir=${1:-$(mktemp -d -t swarm-ci-smoke-XXXXXX)}
mkdir -p "$log_dir"
log_dir=$(cd -- "$log_dir" && pwd)
COMPOSE_PROJECT_NAME="swarm-ci-smoke-$(date +%s)-$$"
export COMPOSE_PROJECT_NAME
# Base-file interpolation happens before the CI override removes GUI mounts.
export DISPLAY=:0 XAUTHORITY=/tmp/swarm-ci.Xauthority
compose=(docker compose --project-directory "$repo_root"
    -f "$repo_root/docker-compose.yml" -f "$repo_root/docker-compose.ci.yml")

cleanup() {
    status=$?
    trap - EXIT
    echo "Collecting logs and cleaning up $COMPOSE_PROJECT_NAME..."
    timeout --kill-after=5s 15s "${compose[@]}" logs --no-color >"$log_dir/containers.log" 2>&1 || true
    timeout --kill-after=5s 15s "${compose[@]}" ps -a >"$log_dir/services.log" 2>&1 || true
    timeout --kill-after=5s 15s "${compose[@]}" cp builder:/workspace/ros2_ws/log "$log_dir/colcon" >/dev/null 2>&1 || true
    if ! timeout --kill-after=5s 60s "${compose[@]}" down --timeout 10 --volumes --remove-orphans --rmi local \
        >"$log_dir/cleanup.log" 2>&1; then
        echo "FAIL: cleanup did not finish; see $log_dir/cleanup.log (project $COMPOSE_PROJECT_NAME)"
        status=1
    fi
    echo "Smoke test finished with exit status $status. Logs: $log_dir"
    exit "$status"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "Smoke-test logs: $log_dir"
"${compose[@]}" config >"$log_dir/compose.yml"
"${compose[@]}" build 2>&1 | tee "$log_dir/images.log"
timeout --kill-after=5s 180s "${compose[@]}" up -d 2>&1 | tee "$log_dir/startup.log"

# Run the ROS observer while monitoring container health. Its wall-clock
# deadline still expires if simulation time stalls or never starts.
"${compose[@]}" exec -T autonomy bash -c \
    'source /workspace/ros2_ws/install/setup.bash && python3 -u /ci/smoke-test.py' \
    >"$log_dir/checks.log" 2>&1 &
observer_pid=$!
deadline=$((SECONDS + 210))
while kill -0 "$observer_pid" 2>/dev/null; do
    for service in gazebo autonomy; do
        container_id=$(timeout --kill-after=5s 10s "${compose[@]}" ps -a -q "$service")
        if [[ -z "$container_id" ]] || \
            [[ $(timeout --kill-after=5s 10s docker inspect --format '{{.State.Running}}' "$container_id") != true ]]; then
            echo "FAIL: $service stopped during smoke test"
            exit 1
        fi
    done
    if (( SECONDS >= deadline )); then
        echo 'FAIL: smoke-test observer exceeded wall-clock deadline'
        exit 1
    fi
    sleep 2
done
observer_status=0
wait "$observer_pid" || observer_status=$?
cat "$log_dir/checks.log"
if (( observer_status != 0 )); then
    exit "$observer_status"
fi

# Confirm actual Gazebo entities, in addition to live ROS interfaces.
echo 'Checking Gazebo scene entities (hard deadline: 20 seconds)...'
# Empty protobuf requests must receive EOF, rather than an open stdin pipe.
if ! timeout --kill-after=5s 15s "${compose[@]}" exec -T --interactive=false gazebo gz service \
    -s /world/empty/scene/info --reqtype gz.msgs.Empty --reptype gz.msgs.Scene \
    --timeout 10000 --req '' >"$log_dir/scene.txt" 2>"$log_dir/scene-error.log"; then
    echo "FAIL: Gazebo scene query failed or timed out; see $log_dir/scene-error.log"
    exit 1
fi
for robot in robot1 robot2 robot3; do
    if ! grep -Eq "^[[:space:]]*name: \"$robot\"$" "$log_dir/scene.txt"; then
        echo "FAIL: Gazebo scene is missing $robot"
        exit 1
    fi
done
echo 'PASS: three Gazebo entities and all ROS readiness checks'
