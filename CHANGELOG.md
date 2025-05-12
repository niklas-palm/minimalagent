# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2025-05-12

### Changed

- **BREAKING CHANGE**: Updated DynamoDB table schema to use standard single-table design
  - Changed `session_id` attribute to `pk` (partition key)
  - Changed `timestamp` attribute to `sk` (sort key)
  - All existing tables will need to be recreated with the new schema
- Changed default log level from ERROR to WARNING to align with Python logging standards
- Improved DynamoDB size limit handling to be more robust and user-friendly
  - Changed from preemptive size checking to exception-based handling
  - Added explicit warning to final response when size limit is exceeded
  - Now keeps full reasoning data until a size exception is encountered

### Added

- Enhanced DynamoDB documentation with comprehensive table structure details
- More detailed explanations of single-table design pattern in README
- Added additional tests for real-time reasoning functionality
- Added comprehensive table showing entity types and their attributes
- Added new `log_level` parameter to control standard logging verbosity
- Completely redesigned logging system with separate pathways for:
  - Standard logging (errors, warnings) using Python's logging module
  - Colorized reasoning display for interactive use (controlled by show_reasoning)
- Added debug logging for all major agent operations
- Improved error logging to always log errors regardless of `show_reasoning` setting
- Enhanced display methods with more distinct color coding and better formatting
- Added `exceeded_size_limit` flag to Reasoning model to indicate when data was truncated
- Added special formatting for info messages to distinguish them from other output

### Fixed

- Improved test coverage for real_time_reasoning feature
- Fixed duplicate log entries by setting logger.propagate=False
- Fixed plain text info messages by adding proper color formatting

## [0.1.0] - 2025-05-10

### Added

- Initial release of MinimalAgent
- Core Agent class with Amazon Bedrock integration
- Tool decorator with automatic docstring parsing
- Session memory support via DynamoDB
- Configurable reasoning display with color formatting
- Dynamic tool management (add/remove tools at runtime)
- Support for system prompts
- Error handling for AWS credentials
- Multiple example scripts

### Security

- Session ID validation to prevent injection attacks
- DynamoDB TTL for automatic data expiration
