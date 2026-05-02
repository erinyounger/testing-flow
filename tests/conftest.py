import pytest
import subprocess
import os
from pathlib import Path


@pytest.fixture
def git_repo(tmp_path):
    """Create temporary git repo"""
    subprocess.run(["git", "init"], cwd=tmp_path, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=tmp_path, capture_output=True
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=tmp_path, capture_output=True
    )
    readme = tmp_path / "README.md"
    readme.write_text("# Test")
    subprocess.run(["git", "add", "README.md"], cwd=tmp_path, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial"],
        cwd=tmp_path, capture_output=True
    )
    return tmp_path


@pytest.fixture(autouse=True)
def change_to_tmp_path(tmp_path):
    """Auto change to tmp directory"""
    original_dir = os.getcwd()
    os.chdir(tmp_path)
    yield
    os.chdir(original_dir)