# ProEthica Integration

This branch (`proethica-integration`) is specifically designed for integration with the ProEthica AI Ethical Decision Making platform.

## Special Features

1. **Claude API Authentication**: Properly configured to handle the Anthropic SDK authentication requirements.
2. **Environment Variable Handling**: Uses run_with_env.sh for enhanced environment variable management.
3. **Mock Fallback Control**: Respects USE_MOCK_FALLBACK setting in .env file.

## Key Integration Points

- **API Integration**: The adapter in `adapters/proethica.py` is customized for the ProEthica platform.
- **Authentication Flow**: Modified to work properly with ProEthica's authentication system.
- **Response Formatting**: Tailored to match ProEthica's expected formats.

## Maintenance

When making changes to this branch, please ensure:

1. All Claude API authentication features remain intact.
2. Changes respect the environment variable loading mechanisms.
3. ProEthica-specific customizations are preserved.

This branch was last updated on April 27, 2025.
