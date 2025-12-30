#!/usr/bin/env python3
"""
CV Bibliography Generator
Generates formatted bibliographies from BibTeX files using pandoc.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path


def generate_bibliography(
    bib_file: str = "pubs.bib",
    csl_file: str = "elsev.csl",
    output_file: str = "pubs.md",
    input_template: str = "temp_nocite.md",
    plain: bool = False,
) -> None:
    """
    Generate a formatted bibliography using pandoc.

    Args:
        bib_file: Path to the BibTeX bibliography file
        csl_file: Path to the CSL citation style file
        output_file: Path to the output file
        input_template: Path to the input markdown file with nocite metadata
        plain: Generate plain text output (better for VS Code)
    """

    # Check if required files exist
    if not Path(bib_file).exists():
        print(f"Error: Bibliography file '{bib_file}' not found.", file=sys.stderr)
        sys.exit(1)

    if not Path(csl_file).exists():
        print(f"Error: CSL file '{csl_file}' not found.", file=sys.stderr)
        sys.exit(1)

    if not Path(input_template).exists():
        print(f"Error: Input template '{input_template}' not found.", file=sys.stderr)
        sys.exit(1)

    # Build pandoc command
    cmd = [
        "pandoc",
        input_template,
        f"--bibliography={bib_file}",
        f"--csl={csl_file}",
        "-o",
        output_file,
        "--citeproc",
    ]

    # Add format options for cleaner output
    if plain or output_file.endswith('.txt'):
        cmd.extend(["-t", "plain", "--wrap=none"])
    elif output_file.endswith('.md'):
        # For markdown, use gfm but we'll clean it up in post-processing
        cmd.extend(["-t", "gfm", "--wrap=none"])

    print(f"Generating bibliography...")
    print(f"  Input: {input_template}")
    print(f"  Bibliography: {bib_file}")
    print(f"  Style: {csl_file}")
    print(f"  Output: {output_file}")
    if plain:
        print(f"  Format: plain text (VS Code friendly)")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)

        # Post-process the output to fix link formatting
        if Path(output_file).exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Clean up HTML tags and fix links for markdown output
            if output_file.endswith('.md'):
                # Remove HTML div and span tags
                content = re.sub(r'<div[^>]*>', '', content)
                content = re.sub(r'</div>', '', content)
                content = re.sub(r'<span[^>]*>', '', content)
                content = re.sub(r'</span>', '', content)
                # Remove sub/sup tags but keep content (handle both escaped and unescaped)
                content = re.sub(r'\\?</?su[bp]\\?>', '', content)
                # Clean up extra blank lines
                content = re.sub(r'\n\n\n+', '\n\n', content)
                content = content.strip()

            # Fix malformed links - replace patterns to get [#](URL) format
            # Pattern 1: Fix escaped brackets with angle-bracketed URLs: \[#\](<URL>)
            content = re.sub(
                r'\\?\[#\\?\]\(<?(https?://[^>)]+)>?\)',
                r'[#](\1)',
                content
            )
            # Pattern 2: Fix escaped brackets with nested links: \[#\](URL[DOI](URL))
            content = re.sub(
                r'\\?\[#\\?\]\((https://doi\.org/)\[([^\]]+)\]\(\1\2\)\)',
                r'[#](\1\2)',
                content
            )
            # Pattern 3: Fix other URL patterns
            content = re.sub(
                r'\\?\[#\\?\]\(([^)]+)\[([^\]]+)\]\(\1\)\)',
                r'[#](\1)',
                content
            )
            # Pattern 4: Simple case - [URL](URL) -> [#](URL)
            content = re.sub(
                r'\[https://doi\.org/([^\]]+)\]\(https://doi\.org/\1\)',
                r'[#](https://doi.org/\1)',
                content
            )
            content = re.sub(
                r'\[(https?://[^\]]+)\]\(\1\)',
                r'[#](\1)',
                content
            )

            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(content)

        print(f"\n✓ Successfully generated {output_file}")

        if result.stdout:
            print(f"\nPandoc output:\n{result.stdout}")

    except subprocess.CalledProcessError as e:
        print(f"\n✗ Error generating bibliography:", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        sys.exit(1)
    except FileNotFoundError:
        print("\n✗ Error: pandoc not found. Please install pandoc.", file=sys.stderr)
        print("  Install with: brew install pandoc (macOS)", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Generate formatted bibliographies from BibTeX files using pandoc."
    )

    parser.add_argument(
        "-b", "--bib",
        default="pubs.bib",
        help="Path to BibTeX bibliography file (default: pubs.bib)"
    )

    parser.add_argument(
        "-c", "--csl",
        default="elsev.csl",
        help="Path to CSL citation style file (default: elsev.csl)"
    )

    parser.add_argument(
        "-o", "--output",
        default="pubs.md",
        help="Path to output file (default: pubs.md)"
    )

    parser.add_argument(
        "-i", "--input",
        default="temp_nocite.md",
        help="Path to input template file (default: temp_nocite.md)"
    )

    parser.add_argument(
        "--formats",
        nargs="+",
        choices=["md", "html", "pdf", "docx", "txt"],
        help="Generate multiple output formats (e.g., --formats md html pdf)"
    )

    parser.add_argument(
        "--plain",
        action="store_true",
        help="Generate plain text output (better for VS Code markdown preview)"
    )

    args = parser.parse_args()

    if args.formats:
        # Generate multiple formats
        for fmt in args.formats:
            output_file = Path(args.output).stem + f".{fmt}"
            generate_bibliography(
                bib_file=args.bib,
                csl_file=args.csl,
                output_file=output_file,
                input_template=args.input,
                plain=args.plain,
            )
    else:
        # Generate single output
        generate_bibliography(
            bib_file=args.bib,
            csl_file=args.csl,
            output_file=args.output,
            input_template=args.input,
            plain=args.plain,
        )


if __name__ == "__main__":
    main()
