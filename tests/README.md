If you're using Visual Studio Code and are having problems with test discovery, try adding the following settings to your workspace's `settings.json`:

```
"python.testing.cwd": "${workspaceFolder}",
"python.testing.pytestPath": ".venv/Scripts/pytest.exe",
```
