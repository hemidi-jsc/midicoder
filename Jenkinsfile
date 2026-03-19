pipeline {
  agent any

  options {
    timestamps()
    ansiColor('xterm')
    disableConcurrentBuilds()
    buildDiscarder(logRotator(numToKeepStr: '30'))
  }

  environment {
    PIP_DISABLE_PIP_VERSION_CHECK = '1'
    PYTHONDONTWRITEBYTECODE = '1'
    PYTHONUNBUFFERED = '1'
    REVIEW_READY_FILE = 'reports/review-ready.txt'
  }

  stages {
    stage('Checkout') {
      steps {
        checkout scm
        sh 'mkdir -p reports'
      }
    }

    stage('Setup') {
      steps {
        sh '''
          python3 -m venv .venv
          . .venv/bin/activate
          python -m pip install --upgrade pip
          python -m pip install -e .[dev]
        '''
      }
    }

    stage('Repo Policy') {
      steps {
        sh '''
          . .venv/bin/activate
          python scripts/ci/check_pr_template.py
          python scripts/ci/check_docs_update.py
        '''
      }
    }

    stage('Lint & Convention') {
      steps {
        sh '''
          . .venv/bin/activate
          CHANGED_PY_FILES=$(python scripts/ci/list_changed_files.py --suffix .py)
          if [ -n "$CHANGED_PY_FILES" ]; then
            echo "$CHANGED_PY_FILES" | xargs ruff check
            echo "$CHANGED_PY_FILES" | xargs ruff format --check
          else
            echo "No changed Python files for Ruff checks."
          fi
          python scripts/ci/check_code_convention.py
        '''
      }
    }

    stage('Unit Tests') {
      steps {
        sh '''
          . .venv/bin/activate
          coverage run --branch -m pytest -m unit midicoder/tests/unit
        '''
      }
    }

    stage('Integration Tests') {
      steps {
        sh '''
          . .venv/bin/activate
          coverage run --branch --append -m pytest -m integration midicoder/tests/integration
        '''
      }
    }

    stage('Coverage Gate') {
      steps {
        sh '''
          . .venv/bin/activate
          coverage xml
          coverage json
          coverage report --fail-under=100
          echo review-ready > "$REVIEW_READY_FILE"
        '''
      }
    }

    stage('Package Smoke') {
      steps {
        sh '''
          . .venv/bin/activate
          python -m compileall midicoder scripts/ci
          python -m pip check
        '''
      }
    }
  }

  post {
    always {
      junit allowEmptyResults: true, testResults: 'reports/junit.xml'
      archiveArtifacts allowEmptyArchive: true, artifacts: 'coverage.xml,coverage.json,reports/**'
      script {
        if (fileExists(env.REVIEW_READY_FILE)) {
          currentBuild.description = 'review-ready: quality gates passed'
        } else {
          currentBuild.description = 'not review-ready: quality gates failed'
        }
      }
    }
  }
}
