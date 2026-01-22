---
name: jenkins
description: Interact with Jenkins CI/CD server. Use for viewing pipeline logs, build status, starting builds, and stopping builds.
argument-hint: [command] [job-name] [build-number]
allowed-tools: Bash(python:*)
---

# Jenkins CI/CD Integration

This skill provides access to Jenkins at `http://XXX.XXX.XXX.XXX:PORT` for viewing pipeline information and managing builds.

## Configuration

Set these environment variables for authentication:
- `JENKINS_USER` - USER-NAME
- `JENKINS_TOKEN` - API-KEY
- `JENKINS_URL` - (Optional) Override default URL `http://XXX.XXX.XXX.XXX:PORT`

## Available Commands

### List Jobs
```bash
python3 ~/.claude/skills/jenkins/scripts/jenkins_cli.py list
python3 ~/.claude/skills/jenkins/scripts/jenkins_cli.py list --folder FolderName
```

### View Job Information
```bash
python3 ~/.claude/skills/jenkins/scripts/jenkins_cli.py info JOB_NAME
```

### View Build Information
```bash
python3 ~/.claude/skills/jenkins/scripts/jenkins_cli.py build-info JOB_NAME BUILD_NUMBER
python3 ~/.claude/skills/jenkins/scripts/jenkins_cli.py build-info JOB_NAME lastBuild
```

### View Build Logs
```bash
python3 ~/.claude/skills/jenkins/scripts/jenkins_cli.py log JOB_NAME BUILD_NUMBER
python3 ~/.claude/skills/jenkins/scripts/jenkins_cli.py log JOB_NAME lastBuild --tail 100
```

### View Pipeline Stages
```bash
python3 ~/.claude/skills/jenkins/scripts/jenkins_cli.py pipeline JOB_NAME BUILD_NUMBER
```

### Start a Build
```bash
python3 ~/.claude/skills/jenkins/scripts/jenkins_cli.py start JOB_NAME
python3 ~/.claude/skills/jenkins/scripts/jenkins_cli.py start JOB_NAME -p PARAM1=value1 -p PARAM2=value2
```

### Stop a Build
```bash
python3 ~/.claude/skills/jenkins/scripts/jenkins_cli.py stop JOB_NAME BUILD_NUMBER
```

### View Build Queue
```bash
python3 ~/.claude/skills/jenkins/scripts/jenkins_cli.py queue
```

### Check Connection
```bash
python3 ~/.claude/skills/jenkins/scripts/jenkins_cli.py check
```

## Usage Instructions

When the user asks about Jenkins, use the appropriate command:

1. **"Show me Jenkins jobs"** or **"List pipelines"** - Use the `list` command
2. **"What's the status of [job]?"** - Use the `info` command
3. **"Show me the logs for [job]"** - Use the `log` command with `lastBuild` or specific build number
4. **"Show pipeline stages"** - Use the `pipeline` command
5. **"Start/run/trigger [job]"** - Use the `start` command
6. **"Stop/abort [job] build"** - Use the `stop` command
7. **"What's in the queue?"** - Use the `queue` command

## Examples

User: "What jobs are available in Jenkins?"
```bash
python3 ~/.claude/skills/jenkins/scripts/jenkins_cli.py list
```

User: "Show me the last build log for my-pipeline"
```bash
python3 ~/.claude/skills/jenkins/scripts/jenkins_cli.py log my-pipeline lastBuild
```

User: "Start the deploy-prod job with version 1.2.3"
```bash
python3 ~/.claude/skills/jenkins/scripts/jenkins_cli.py start deploy-prod -p VERSION=1.2.3
```

User: "Stop build 42 of the test-pipeline job"
```bash
python3 ~/.claude/skills/jenkins/scripts/jenkins_cli.py stop test-pipeline 42
```
