# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
