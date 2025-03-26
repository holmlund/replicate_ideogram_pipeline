# Replicate Ideogram Pipeline

A powerful image generation pipeline for Open-Webui that integrates with Replicate's Ideogram v2a API. This pipeline provides a flexible and intuitive way to generate high-quality images using command-line style parameters.

## Description

This project provides a Python-based pipeline that interfaces with Replicate's Ideogram API, offering a wide range of image generation capabilities. It supports various styles, aspect ratios, and resolutions, making it versatile for different use cases:

- Multiple style options (Auto, General, Realistic, Design, Render 3D, Anime)
- Various aspect ratios (1:1, 16:9, 4:3 etc.)
- Extensive resolution options
- Command-line style parameter input
- Automatic parameter matching with fuzzy search
- Markdown-formatted image output

## Features

- Command-line style parameter parsing with support for quoted strings
- Fuzzy matching for styles, aspect ratios, and resolutions
- Comprehensive resolution support with validation
- Robust error handling and parameter validation
- Markdown-formatted responses for Open-WebUI compatibility

## Installation

Add as a pipeline in Open-WebUI.

## Configuration

The pipeline requires a Replicate API token which can be configured in two ways:
1. Environment variable: `REPLICATE_API_TOKEN`
2. Valve configuration: `REPLICATE_API_TOKEN`

## Usage Examples

```
A birthday cake with candles and frosting, decorated with the text 'dev/null' written on top. --style Realistic --aspect 1:1 

A minimalist interior design with a sleek scandinavian coffee table, a single elegant coffee cup on top, and the word "More coffee is the answer!" displayed in striking art deco letters as part of the wall, set against a soft neutral color palette for a modern and striking visual contrast.--style Design --aspect 4:3 --res 1280x960

A cute robot in a garden with a speech bubble that says "Hello World" --style Anime --aspect 1:1
```

## Response Format

The pipeline returns markdown-formatted strings:
- Success: `![image](https://replicate.delivery/...)`
- Error: `Error: <error message>`

## Resolution Handling

The pipeline supports a wide range of predefined resolutions (e.g., 1024x1024, 1280x768, 1536x640). Resolution overrides aspect ratio when specified, with automatic fallback to aspect ratio if the resolution is invalid. The pipeline includes fuzzy matching and validation for resolution input.

When resolution errors occur (invalid format, non-numeric values, etc.), the pipeline falls back to the specified aspect ratio or defaults to 1:1.

## License

This project is licensed under the MIT License.

## Acknowledgments

- Sponsored by Digitalist Open Tech
- Built with Replicate's Ideogram API 