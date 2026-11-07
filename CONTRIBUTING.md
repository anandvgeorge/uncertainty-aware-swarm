# Contributing Guidelines

## 1. Branching Strategy

- `main`: Stable and tested releases.
- `dev`: Integration branch.
- `feature/*`: New functionality.
- `fix/*`: Bug fixes.
- `docs/*`: Documentation changes.

Create feature branches from `dev`.

## 2. Development Workflow

1. Identify or create a GitHub Issue.
2. Create a branch from `dev`.
3. Implement the changes.
4. Add or update tests.
5. Commit changes.
6. Push the branch to GitHub.
7. Open a Pull Request targeting `dev`.
8. Review and merge the PR.

Do not push feature implementation directly to `dev`.

## 3. Commit Convention

Use conventional commit prefixes:

| Prefix | Purpose |
|---|---|
| `feat:` | New functionality |
| `fix:` | Bug fixes |
| `test:` | Tests |
| `docs:` | Documentation |
| `refactor:` | Code restructuring |
| `build:` | Build configuration |
| `ci:` | CI configuration |
| `chore:` | Maintenance |

Example:

```bash
git commit -m "feat: implement RVO collision avoidance"
```

Keep commits small and logically independent.

## 4. Coding Guidelines

- Use C++17.
- Follow ROS 2 package conventions.
- Prefer modular, reusable components.
- Separate algorithm implementations from ROS interfaces.
- Document public interfaces.
- Avoid unnecessary dependencies.

## 5. Testing

- Add unit tests for algorithmic components.
- Use GoogleTest for C++ tests.
- Test ROS integration separately.
- Ensure existing tests pass before submitting PRs.

## 6. Pull Requests

Every PR should:

- Target `dev`.
- Reference relevant GitHub Issues.
- Explain the changes and motivation.
- Include testing instructions and results.
- Update relevant documentation.
- Pass applicable CI checks.

Keep PRs focused on a coherent implementation task.