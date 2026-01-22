#!/usr/bin/env python3
"""
Jenkins CLI tool for Claude Code skill integration.
Provides read access to Jenkins pipelines, logs, and build management.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error
import urllib.parse
import base64
from typing import Optional

JENKINS_URL = os.environ.get("JENKINS_URL", "http://XXX.XXX.XXX.XXX:PORT")
JENKINS_USER = os.environ.get("JENKINS_USER", "")
JENKINS_TOKEN = os.environ.get("JENKINS_TOKEN", "")


def get_auth_header() -> dict:
    """Build authorization header if credentials are set."""
    if JENKINS_USER and JENKINS_TOKEN:
        credentials = f"{JENKINS_USER}:{JENKINS_TOKEN}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {"Authorization": f"Basic {encoded}"}
    return {}


def make_request(path: str, method: str = "GET", data: Optional[bytes] = None) -> tuple:
    """Make HTTP request to Jenkins API."""
    url = f"{JENKINS_URL.rstrip('/')}/{path.lstrip('/')}"
    headers = get_auth_header()
    headers["Content-Type"] = "application/x-www-form-urlencoded"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            content = response.read().decode("utf-8")
            return response.status, content
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        return 0, f"Connection error: {e.reason}"
    except Exception as e:
        return 0, f"Error: {str(e)}"


def list_jobs(folder: Optional[str] = None) -> None:
    """List all Jenkins jobs."""
    path = "api/json?tree=jobs[name,color,url,lastBuild[number,result,timestamp]]"
    if folder:
        path = f"job/{urllib.parse.quote(folder, safe='')}/api/json?tree=jobs[name,color,url,lastBuild[number,result,timestamp]]"

    status, content = make_request(path)

    if status != 200:
        print(f"Error ({status}): {content}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(content)
        jobs = data.get("jobs", [])

        if not jobs:
            print("No jobs found.")
            return

        print(f"{'Job Name':<40} {'Status':<15} {'Last Build':<10} {'Result':<12}")
        print("-" * 80)

        for job in jobs:
            name = job.get("name", "Unknown")
            color = job.get("color", "notbuilt")
            last_build = job.get("lastBuild") or {}
            build_num = last_build.get("number", "-")
            result = last_build.get("result", "N/A") or "BUILDING"

            status_map = {
                "blue": "Stable",
                "blue_anime": "Building",
                "red": "Failed",
                "red_anime": "Building",
                "yellow": "Unstable",
                "yellow_anime": "Building",
                "grey": "Pending",
                "disabled": "Disabled",
                "notbuilt": "Not Built",
            }
            status_text = status_map.get(color, color)

            print(f"{name:<40} {status_text:<15} {str(build_num):<10} {result:<12}")

    except json.JSONDecodeError:
        print(f"Invalid JSON response: {content[:200]}", file=sys.stderr)
        sys.exit(1)


def get_job_info(job_name: str) -> None:
    """Get detailed information about a specific job."""
    encoded_name = urllib.parse.quote(job_name, safe='')
    path = f"job/{encoded_name}/api/json?tree=name,description,color,buildable,lastBuild[number,result,timestamp,duration],lastSuccessfulBuild[number],lastFailedBuild[number],nextBuildNumber,healthReport[description,score]"

    status, content = make_request(path)

    if status != 200:
        print(f"Error ({status}): {content}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(content)

        print(f"Job: {data.get('name', job_name)}")
        print(f"Description: {data.get('description') or 'No description'}")
        print(f"Buildable: {data.get('buildable', False)}")
        print(f"Next Build Number: {data.get('nextBuildNumber', 'N/A')}")

        if data.get("healthReport"):
            print("\nHealth Reports:")
            for report in data["healthReport"]:
                print(f"  - {report.get('description', 'N/A')} (Score: {report.get('score', 'N/A')})")

        last_build = data.get("lastBuild")
        if last_build:
            duration_ms = last_build.get("duration", 0)
            duration_sec = duration_ms // 1000
            print(f"\nLast Build: #{last_build.get('number')}")
            print(f"  Result: {last_build.get('result') or 'BUILDING'}")
            print(f"  Duration: {duration_sec // 60}m {duration_sec % 60}s")

        if data.get("lastSuccessfulBuild"):
            print(f"Last Successful Build: #{data['lastSuccessfulBuild'].get('number')}")
        if data.get("lastFailedBuild"):
            print(f"Last Failed Build: #{data['lastFailedBuild'].get('number')}")

    except json.JSONDecodeError:
        print(f"Invalid JSON response: {content[:200]}", file=sys.stderr)
        sys.exit(1)


def get_build_info(job_name: str, build_number: str) -> None:
    """Get information about a specific build."""
    encoded_name = urllib.parse.quote(job_name, safe='')
    path = f"job/{encoded_name}/{build_number}/api/json"

    status, content = make_request(path)

    if status != 200:
        print(f"Error ({status}): {content}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(content)

        duration_ms = data.get("duration", 0)
        duration_sec = duration_ms // 1000

        print(f"Build: {data.get('fullDisplayName', f'{job_name} #{build_number}')}")
        print(f"Result: {data.get('result') or 'BUILDING'}")
        print(f"Building: {data.get('building', False)}")
        print(f"Duration: {duration_sec // 60}m {duration_sec % 60}s")
        print(f"URL: {data.get('url', 'N/A')}")

        if data.get("changeSets"):
            print("\nChanges:")
            for changeset in data["changeSets"]:
                for item in changeset.get("items", []):
                    msg = item.get("msg", "No message")[:60]
                    author = item.get("author", {}).get("fullName", "Unknown")
                    print(f"  - {msg} ({author})")

        if data.get("actions"):
            for action in data["actions"]:
                if action.get("_class", "").endswith("ParametersAction"):
                    print("\nParameters:")
                    for param in action.get("parameters", []):
                        print(f"  {param.get('name')}: {param.get('value')}")

    except json.JSONDecodeError:
        print(f"Invalid JSON response: {content[:200]}", file=sys.stderr)
        sys.exit(1)


def get_build_log(job_name: str, build_number: str, tail: Optional[int] = None) -> None:
    """Get console output for a build."""
    encoded_name = urllib.parse.quote(job_name, safe='')
    path = f"job/{encoded_name}/{build_number}/consoleText"

    status, content = make_request(path)

    if status != 200:
        print(f"Error ({status}): {content}", file=sys.stderr)
        sys.exit(1)

    if tail:
        lines = content.split("\n")
        content = "\n".join(lines[-tail:])

    print(content)


def get_pipeline_log(job_name: str, build_number: str) -> None:
    """Get pipeline stages and their logs."""
    encoded_name = urllib.parse.quote(job_name, safe='')

    # Get workflow run info
    path = f"job/{encoded_name}/{build_number}/wfapi/describe"
    status, content = make_request(path)

    if status != 200:
        # Fall back to regular console log
        print("Note: Pipeline API not available, showing console log instead.\n")
        get_build_log(job_name, build_number)
        return

    try:
        data = json.loads(content)

        print(f"Pipeline: {data.get('name', job_name)}")
        print(f"Status: {data.get('status', 'UNKNOWN')}")

        duration_ms = data.get("durationMillis", 0)
        duration_sec = duration_ms // 1000
        print(f"Duration: {duration_sec // 60}m {duration_sec % 60}s")

        stages = data.get("stages", [])
        if stages:
            print(f"\nStages ({len(stages)}):")
            print("-" * 60)
            for stage in stages:
                stage_name = stage.get("name", "Unknown")
                stage_status = stage.get("status", "UNKNOWN")
                stage_duration = stage.get("durationMillis", 0) // 1000
                print(f"  {stage_name:<30} {stage_status:<12} {stage_duration}s")

    except json.JSONDecodeError:
        print(f"Invalid JSON response: {content[:200]}", file=sys.stderr)
        sys.exit(1)


def start_build(job_name: str, params: Optional[list] = None) -> None:
    """Start a new build for a job."""
    encoded_name = urllib.parse.quote(job_name, safe='')

    if params:
        path = f"job/{encoded_name}/buildWithParameters"
        param_dict = {}
        for p in params:
            if "=" in p:
                key, value = p.split("=", 1)
                param_dict[key] = value
        data = urllib.parse.urlencode(param_dict).encode()
    else:
        path = f"job/{encoded_name}/build"
        data = None

    status, content = make_request(path, method="POST", data=data)

    if status in (200, 201, 302):
        print(f"Build started successfully for job: {job_name}")
        # Get queue info
        queue_path = f"job/{encoded_name}/api/json?tree=queueItem[id,why],lastBuild[number]"
        q_status, q_content = make_request(queue_path)
        if q_status == 200:
            try:
                q_data = json.loads(q_content)
                if q_data.get("queueItem"):
                    print(f"Queue ID: {q_data['queueItem'].get('id')}")
                    if q_data['queueItem'].get('why'):
                        print(f"Status: {q_data['queueItem']['why']}")
                elif q_data.get("lastBuild"):
                    print(f"Last build number: #{q_data['lastBuild'].get('number')}")
            except json.JSONDecodeError:
                pass
    else:
        print(f"Error starting build ({status}): {content}", file=sys.stderr)
        sys.exit(1)


def stop_build(job_name: str, build_number: str) -> None:
    """Stop a running build."""
    encoded_name = urllib.parse.quote(job_name, safe='')
    path = f"job/{encoded_name}/{build_number}/stop"

    status, content = make_request(path, method="POST")

    if status in (200, 302):
        print(f"Build #{build_number} stopped for job: {job_name}")
    else:
        print(f"Error stopping build ({status}): {content}", file=sys.stderr)
        sys.exit(1)


def get_queue() -> None:
    """Get current build queue."""
    path = "queue/api/json"
    status, content = make_request(path)

    if status != 200:
        print(f"Error ({status}): {content}", file=sys.stderr)
        sys.exit(1)

    try:
        data = json.loads(content)
        items = data.get("items", [])

        if not items:
            print("Build queue is empty.")
            return

        print(f"{'ID':<8} {'Job':<40} {'Why':<40}")
        print("-" * 90)

        for item in items:
            item_id = item.get("id", "?")
            task = item.get("task", {})
            job_name = task.get("name", "Unknown")
            why = item.get("why", "N/A")[:40]
            print(f"{item_id:<8} {job_name:<40} {why:<40}")

    except json.JSONDecodeError:
        print(f"Invalid JSON response: {content[:200]}", file=sys.stderr)
        sys.exit(1)


def check_connection() -> None:
    """Check Jenkins connectivity and authentication."""
    status, content = make_request("api/json?tree=mode,nodeDescription,useSecurity")

    if status == 0:
        print(f"Cannot connect to Jenkins at {JENKINS_URL}")
        print(f"Error: {content}")
        sys.exit(1)
    elif status == 401:
        print(f"Authentication required. Set JENKINS_USER and JENKINS_TOKEN environment variables.")
        sys.exit(1)
    elif status == 403:
        print(f"Access forbidden. Check your Jenkins credentials and permissions.")
        sys.exit(1)
    elif status != 200:
        print(f"Unexpected response ({status}): {content[:200]}")
        sys.exit(1)

    try:
        data = json.loads(content)
        print(f"Connected to Jenkins at {JENKINS_URL}")
        print(f"Mode: {data.get('mode', 'Unknown')}")
        print(f"Description: {data.get('nodeDescription', 'N/A')}")
        print(f"Security Enabled: {data.get('useSecurity', False)}")
    except json.JSONDecodeError:
        print(f"Connected to Jenkins at {JENKINS_URL}")


def main():
    parser = argparse.ArgumentParser(
        description="Jenkins CLI for Claude Code",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list                          List all jobs
  %(prog)s list --folder MyFolder        List jobs in a folder
  %(prog)s info my-job                   Get job details
  %(prog)s build-info my-job 42          Get build #42 info
  %(prog)s log my-job 42                 Get build log
  %(prog)s log my-job 42 --tail 50       Get last 50 lines
  %(prog)s pipeline my-job 42            Get pipeline stages
  %(prog)s start my-job                  Start a build
  %(prog)s start my-job -p KEY=VALUE     Start with parameters
  %(prog)s stop my-job 42                Stop build #42
  %(prog)s queue                         Show build queue
  %(prog)s check                         Check connection

Environment Variables:
  JENKINS_URL    Jenkins server URL (default: http://XXX.XXX.XXX.XXX:PORT)
  JENKINS_USER   Username for authentication
  JENKINS_TOKEN  API token or password
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # List jobs
    list_parser = subparsers.add_parser("list", help="List all jobs")
    list_parser.add_argument("--folder", "-f", help="Folder name to list jobs from")

    # Job info
    info_parser = subparsers.add_parser("info", help="Get job information")
    info_parser.add_argument("job", help="Job name")

    # Build info
    build_parser = subparsers.add_parser("build-info", help="Get build information")
    build_parser.add_argument("job", help="Job name")
    build_parser.add_argument("build", help="Build number (or 'lastBuild')")

    # Console log
    log_parser = subparsers.add_parser("log", help="Get build console log")
    log_parser.add_argument("job", help="Job name")
    log_parser.add_argument("build", help="Build number (or 'lastBuild')")
    log_parser.add_argument("--tail", "-t", type=int, help="Show only last N lines")

    # Pipeline log
    pipeline_parser = subparsers.add_parser("pipeline", help="Get pipeline stages and status")
    pipeline_parser.add_argument("job", help="Job name")
    pipeline_parser.add_argument("build", help="Build number (or 'lastBuild')")

    # Start build
    start_parser = subparsers.add_parser("start", help="Start a new build")
    start_parser.add_argument("job", help="Job name")
    start_parser.add_argument("-p", "--param", action="append", help="Build parameter (KEY=VALUE)")

    # Stop build
    stop_parser = subparsers.add_parser("stop", help="Stop a running build")
    stop_parser.add_argument("job", help="Job name")
    stop_parser.add_argument("build", help="Build number")

    # Queue
    subparsers.add_parser("queue", help="Show build queue")

    # Check connection
    subparsers.add_parser("check", help="Check Jenkins connection")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "list":
        list_jobs(args.folder)
    elif args.command == "info":
        get_job_info(args.job)
    elif args.command == "build-info":
        get_build_info(args.job, args.build)
    elif args.command == "log":
        get_build_log(args.job, args.build, args.tail)
    elif args.command == "pipeline":
        get_pipeline_log(args.job, args.build)
    elif args.command == "start":
        start_build(args.job, args.param)
    elif args.command == "stop":
        stop_build(args.job, args.build)
    elif args.command == "queue":
        get_queue()
    elif args.command == "check":
        check_connection()


if __name__ == "__main__":
    main()
