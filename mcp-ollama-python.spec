# -*- mode: python ; coding: utf-8 -*-
# from terminal/cli, run: poetry shell & pyinstaller mcp-ollama-python.spec --clean --distpath bin
# or from poetry, run: poetry run pyinstaller mcp-ollama-python.spec --clean --distpath bin

block_cipher = None

a = Analysis(
    ['src/mcp_ollama_python/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Standard library
        'asyncio',
        'signal',
        'sys',
        'typing',
        # Timezone data
        'tzdata',
        # MCP dependencies
        'mcp',
        'mcp.server',
        'mcp.server.stdio',
        'mcp.types',
        'mcp.shared',
        'mcp.shared.memory',
        # HTTP client
        'httpx',
        'httpx._transports',
        'httpx._transports.default',
        # Pydantic
        'pydantic',
        'pydantic.fields',
        'pydantic_core',
        # Rich console
        'rich',
        'rich.console',
        'rich.logging',
        # System utilities
        'psutil',
        # JSON handling
        'json',
        'jsonschema',
        # Internal modules
        'mcp_ollama_python',
        'mcp_ollama_python.server',
        'mcp_ollama_python.ollama_client',
        'mcp_ollama_python.models',
        'mcp_ollama_python.response_formatter',
        'mcp_ollama_python.autoloader',
        'mcp_ollama_python.tools',
        'mcp_ollama_python.tools.chat',
        'mcp_ollama_python.tools.delete',
        'mcp_ollama_python.tools.embed',
        'mcp_ollama_python.tools.generate',
        'mcp_ollama_python.tools.list',
        'mcp_ollama_python.tools.ps',
        'mcp_ollama_python.tools.pull',
        'mcp_ollama_python.tools.show',
        # Async support
        'anyio',
        'anyio._backends',
        'anyio._backends._asyncio',
        'sniffio',
        # SSL/HTTP support
        'certifi',
        'httpcore',
        'h11',
        'idna',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='mcp-ollama-python',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
