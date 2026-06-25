# Task Completion Checklist

When a coding task is completed, run the following:

1. **Format code**:
   ```bash
   ruff format .
   ```

2. **Lint code**:
   ```bash
   ruff check . --fix
   ```

3. **Type check** (if Python files were modified):
   ```bash
   pyright
   ```

4. **Run tests** (if authentication/hasher code was modified):
   ```bash
   pytest
   ```

5. **Verify Django startup** (if settings/urls/views were modified):
   ```bash
   python manage.py check
   ```

Note: Git hooks are currently disabled (`git-hooks.enable = false` in devenv.nix).
