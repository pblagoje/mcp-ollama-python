# Development

This guide is for contributors who want to work on the `mcp-ollama-python` codebase itself. If you just want to **use** the server, see [Installation](installation.md).

## Dev Setup

```bash
# Clone and install with all dependency groups
git clone https://github.com/pblagoje/mcp-ollama-python.git
cd mcp-ollama-python
py -m poetry install

# Run the server locally
py -m poetry run mcp-ollama-python
```

## Testing

```bash
py -m poetry run pytest
```

## Code Quality

```bash
# Format
py -m poetry run black src/

# Lint
py -m poetry run flake8 src/

# Pre-commit hooks (install once, runs on every commit)
py -m poetry run pre-commit install
py -m poetry run pre-commit run --all-files
```

## Building the Windows Executable

```bash
poetry run pyinstaller mcp-ollama-python.spec --clean --distpath bin
```

The spec file reads the version from `pyproject.toml` and produces an EXE named like `mcp-ollama-python-1.0.3-win11-x64.exe`.

## Building the Docs

```bash
# Install docs dependencies
py -m poetry install --with docs

# Live preview
py -m poetry run mkdocs serve

# Build static site
py -m poetry run mkdocs build --strict
```

Docs are auto-deployed to GitHub Pages on push to `main` via the `docs.yml` workflow.

## Contributing

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Write tests** for your changes
4. **Commit** with clear messages (`git commit -m 'Add amazing feature'`)
5. **Push** to your branch (`git push origin feature/amazing-feature`)
6. **Open** a Pull Request

### Code Quality Standards

- All new tools must export `tool_definition`
- Maintain comprehensive test coverage
- Follow existing Python patterns (Black formatting, Pydantic schemas)
- See [Architecture](architecture.md) for how to add new tools

## Related Projects

- [ollama-mcp (TypeScript)](https://github.com/rawveg/ollama-mcp) — Original TypeScript implementation
- [Ollama](https://ollama.ai) — Get up and running with large language models locally
- [Model Context Protocol](https://github.com/anthropics/model-context-protocol) — Open standard for AI assistant integration
- [Windsurf](https://codeium.com/windsurf) — AI-powered code editor with MCP support
- [Cline](https://github.com/cline/cline) — VS Code AI assistant
