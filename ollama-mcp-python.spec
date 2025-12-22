# -*- mode: python ; coding: utf-8 -*-
# pyinstaller ollama-mcp-python.spec --clean

block_cipher = None

a = Analysis(
    ['src/ollama_mcp_python/main.py'],
    pathex=['src'],
    binaries=[],
    datas=[],
    hiddenimports=[
        # Standard library
        'asyncio',
        'signal',
        'sys',
        'typing',
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
        'ollama_mcp_python',
        'ollama_mcp_python.server',
        'ollama_mcp_python.ollama_client',
        'ollama_mcp_python.models',
        'ollama_mcp_python.response_formatter',
        'ollama_mcp_python.autoloader',
        'ollama_mcp_python.tools',
        'ollama_mcp_python.tools.chat',
        'ollama_mcp_python.tools.delete',
        'ollama_mcp_python.tools.embed',
        'ollama_mcp_python.tools.generate',
        'ollama_mcp_python.tools.list',
        'ollama_mcp_python.tools.ps',
        'ollama_mcp_python.tools.pull',
        'ollama_mcp_python.tools.show',
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
    name='ollama-mcp-python',
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
