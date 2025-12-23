# Contributing to RAG ADB System

Thank you for your interest in contributing to the RAG System for Advanced Database Course! This document provides guidelines for contributing.

---

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment. Please:

- Be respectful of differing viewpoints
- Accept constructive criticism gracefully
- Focus on what is best for the project
- Show empathy towards other contributors

---

## How to Contribute

### Reporting Bugs

1. **Search existing issues** to avoid duplicates
2. **Use the bug report template** when creating new issues
3. **Include**:
   - Clear title and description
   - Steps to reproduce
   - Expected vs actual behavior
   - Environment details (OS, Python version)
   - Screenshots if applicable

### Suggesting Features

1. **Search existing issues** for similar suggestions
2. **Use the feature request template**
3. **Describe**:
   - The problem you're trying to solve
   - Your proposed solution
   - Alternative approaches considered

### Submitting Code

1. **Fork** the repository
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**:
   - Follow the code style guide
   - Add tests for new functionality
   - Update documentation if needed
4. **Commit with clear messages**:
   ```bash
   git commit -m "feat: add your feature description"
   ```
5. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```
6. **Open a Pull Request**

---

## Pull Request Guidelines

### Before Submitting

- [ ] Code follows project style guidelines
- [ ] Tests pass locally (`pytest tests/`)
- [ ] New code has appropriate tests
- [ ] Documentation is updated
- [ ] Commit messages follow convention

### PR Description

Include:
- **What** changes were made
- **Why** the changes are needed
- **How** to test the changes
- **Screenshots** for UI changes

### Review Process

1. Maintainers will review within 1-2 weeks
2. Address any requested changes
3. Once approved, PR will be merged
4. Your contribution will be acknowledged

---

## Development Setup

See [Development Guide](docs/development.md) for detailed setup instructions.

Quick start:
```bash
git clone https://github.com/YOUR_USERNAME/rag-adb-system.git
cd rag-adb-system
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

---

## Code Style

- **PEP 8** for Python code
- **Type hints** for function signatures
- **Google-style docstrings**
- **Black** for formatting
- **isort** for import sorting

Run before committing:
```bash
black src/ tests/
isort src/ tests/
flake8 src/ tests/
```

---

## Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting (no code change)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

**Examples**:
```
feat(retriever): add semantic weight configuration
fix(generator): handle API timeout gracefully
docs(readme): update installation instructions
```

---

## Questions?

- Open an issue for general questions
- Check documentation first
- Be patient - maintainers volunteer their time

---

Thank you for contributing! 🎉
