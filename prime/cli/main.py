"""
Main CLI entry point for PRIME Voice Assistant.
"""

import argparse
import sys
from pathlib import Path

from prime.utils.logging_config import setup_logging, get_logger


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog="prime",
        description="PRIME Voice Assistant - Proactive Reasoning Intelligent Machine Entity",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.1.0",
    )
    
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Disable voice input/output and use text-only mode",
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level (default: INFO)",
    )
    
    parser.add_argument(
        "--log-dir",
        type=Path,
        help="Directory for log files (default: ~/.prime/logs)",
    )
    
    parser.add_argument(
        "--no-console-log",
        action="store_true",
        help="Disable console logging output",
    )
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for PRIME Voice Assistant.
    
    Returns:
        Exit code (0 for success, non-zero for error)
    """
    # Parse command-line arguments
    args = parse_arguments()
    
    # Setup logging
    setup_logging(
        log_level=args.log_level,
        log_dir=args.log_dir,
        console_output=not args.no_console_log,
        file_output=True,
    )
    
    logger = get_logger(__name__)
    logger.info("Starting PRIME Voice Assistant")
    logger.info(f"Text-only mode: {args.text_only}")
    
    try:
        # TODO: Initialize and start PRIME application
        # This will be implemented in later tasks
        logger.info("PRIME initialization complete")
        logger.info("PRIME is ready (placeholder - full implementation pending)")
        
        # Placeholder message
        print("\n" + "="*60)
        print("PRIME Voice Assistant v0.1.0")
        print("="*60)
        print("\nProject structure initialized successfully!")
        print("\nNext steps:")
        print("  1. Implement core data models (Task 1.2)")
        print("  2. Set up testing framework (Task 1.3)")
        print("  3. Implement persistence layer (Task 2.x)")
        print("\nNote: Full functionality will be available after completing")
        print("      all implementation tasks.")
        print("="*60 + "\n")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("PRIME shutdown requested by user")
        print("\nShutting down PRIME...")
        return 0
        
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        print(f"\nError: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
