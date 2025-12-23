# Changelog

All notable changes to tongyi-cli-interactive will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0-beta.1] - 2025-12-23

### Added

#### Major Features
- 🎨 Modern interactive CLI with rich terminal interface using Rich library
- 💾 Session management with persistent history to `~/.tongyi_agent_history.json`
- ⚡ Interactive commands: help, tools, history, clear, context, status, exit
- 🛠 Tool integration: search_code, read_file, run_sandbox, search_papers, clean_csv, clean_markdown, summarize_results
- 🏗 Model management system with model switching, search, and listing
- 🔧 Configuration management via INI files (`models.ini`)
- 🔒 Security: path traversal protection, data sanitization, input validation
- 📊 Performance metrics tracking and display

#### Enhanced Error Handling (BETA-3)
- Custom exception classes: TongyiAgentError, ConfigurationError, APIKeyError, NetworkError, RateLimitError, ModelNotFoundError, ValidationError, TimeoutError
- Retry mechanisms with exponential backoff and random jitter
- Graceful fallbacks for API failures
- User-friendly error messages with troubleshooting steps
- Input validation with clear error messages

#### Performance Optimizations (BETA-6)
- Caching system with in-memory and file-based persistence
- Cache statistics tracking (hits, misses, hit rate, evictions)
- Memory optimizations for large files (chunked reading, streaming)
- Performance metrics in `status` command
- File snippet caching (<10KB)

#### Agent Lightning Integration
- Complete wrapper system for Agent Lightning
- Training capabilities with statistics tracking
- Graceful degradation when Agent Lightning not installed

#### Claude Agent SDK Integration
- Async support with full tool integration
- Specific timeout handling for async operations
- Error handling for import/connection failures

#### Configuration Validation Tool
- `config_validator.py` CLI tool for validating setup
- API key validation and connection testing
- Model availability checking
- Setup troubleshooting guide

#### Documentation
- Comprehensive documentation suite:
  - README.md - Main documentation and features overview
  - CLI_GUIDE.md - Complete CLI reference
  - INSTALLATION_GUIDE.md - Installation and setup
  - SETUP_TROUBLESHOOTING.md - Troubleshooting guide
  - QUICKSTART.md - 5-minute getting started guide
  - MODEL_MANAGEMENT_GUIDE.md - Model configuration
  - CONTRIBUTING.md - Development and contribution guide
  - RELEASE_NOTES.md - Release notes
  - CHANGELOG.md - Version history

### Fixed

#### BETA-1 Critical Fixes
- Fixed missing `STDIO_LIMIT` constant in `src/sandbox_exec.py` (5 tests)
- Implemented abstract `run()` method in ClaudeAgentOrchestrator (6 tests)
- Fixed API key validation test behavior (1 test)
- Achieved 100% test pass rate (96/96 tests passing)

#### Other Fixes
- Fixed Unicode handling issues on Windows CLI - replaced with ASCII equivalents
- Fixed memory usage high for large files - added chunked processing
- Fixed error messages not user-friendly - comprehensive error handling system
- Fixed incomplete implementations across multiple modules

#### Security Fixes
- Fixed path traversal vulnerability in export - comprehensive validation added
- Fixed data sanitization missing sensitive info - export now properly sanitizes data
- Fixed CLI emoji causing crashes on Windows - replaced with ASCII equivalents

### Changed

- Package name changed from `tongyi-agent` to `tongyi-cli-interactive`
- Version format now follows semantic versioning with beta releases
- Minimum Python version increased to 3.11
- Entry points: `tongyi` and `tongyi-cli` both map to `tongyi_agent.cli:main`

### Testing

- 100% test pass rate (96/96 tests passing)
- 8/8 security tests passing
- All integration tests passing
- Test coverage maintained at or above 95%

### Performance

- Cache hit rate target: 50-70% in production
- API response time: <3s average (with caching)
- Memory usage: <150MB for typical operations
- Startup time: <2s

### Documentation

- Comprehensive documentation suite created
- Installation guides for PyPI and source
- Troubleshooting guides with common issues
- CLI reference with all commands
- API usage examples

---

## [0.1.0] - 2025-10-31

### Added
- Initial alpha release of tongyi-cli-interactive
- Basic CLI functionality
- Tool integration (search_code, read_file, run_sandbox)
- Session management
- Configuration via environment variables

### Known Issues
- Incomplete implementations with pass statements
- Basic error handling
- No caching mechanism
- Limited documentation

---

## Future Releases

### [1.1.0-beta] - Planned: 2026-01-30
- Plugin system foundation
- Web interface prototype
- Advanced caching features
- Comprehensive API documentation

### [2.0.0] - Planned: Future
- Full plugin ecosystem
- Multi-user support
- Enterprise features
- Advanced analytics dashboard

---

## Links

- [GitHub Repository](https://github.com/your-org/tongyi-agent)
- [Issues](https://github.com/your-org/tongyi-agent/issues)
- [Documentation](https://github.com/your-org/tongyi-agent#readme)
