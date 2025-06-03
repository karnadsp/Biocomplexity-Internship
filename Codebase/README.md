# Biological System Modeling Assistant

This tool helps generate CompuCell3D models from biological system descriptions using AI assistance.

## Setup

1. Install the required dependencies:
```bash
pip install python-dotenv deepseek
```

2. Create a `.env` file in the project root with your DeepSeek API key:
```
DEEPSEEK_API_KEY=your_api_key_here
```

3. Run the script:
```bash
python experimental_code.py
```

## Security Note

Never commit your `.env` file to version control. The `.gitignore` file is configured to prevent this.

## Output

The script will create an `experiments` directory containing:
- Individual JSON files for each interaction
- A complete experiment summary
- Generated CC3D model files

Each experiment run is timestamped and organized in its own directory. 