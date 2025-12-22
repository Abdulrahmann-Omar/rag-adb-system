"""
CLI interface for ADB Course RAG System.
Provides command-line access to building index and querying.
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.self_learning import SelfLearningRAG
from src.config import config
from src.utils import print_banner, validate_environment


def build_index(force: bool = False):
    """Build or rebuild the search index."""
    print("\n📚 Building RAG Index...")
    print("-" * 40)
    
    rag = SelfLearningRAG()
    success = rag.initialize(force_rebuild=force)
    
    if success:
        print("\n✅ Index built successfully!")
        stats = rag.pipeline.retriever.get_statistics()
        print(f"   Documents indexed: {stats.get('num_documents', 0)}")
    else:
        print("\n❌ Failed to build index.")
        sys.exit(1)


def query_interactive():
    """Run interactive query mode."""
    print("\n🔍 Interactive Query Mode")
    print("   Type 'exit' or 'quit' to stop")
    print("   Type 'stats' to see statistics")
    print("-" * 40)
    
    rag = SelfLearningRAG()
    
    if not rag.is_ready:
        print("Building index first...")
        rag.initialize()
    
    while True:
        try:
            query = input("\n❓ Your question: ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                break
            
            if query.lower() == 'stats':
                stats = rag.get_learning_stats()
                print(f"\n📊 Learning Stats: {stats}")
                continue
            
            # Process query
            result, metadata = rag.query(query)
            
            # Show expansion info
            if metadata.get('was_expanded'):
                print(f"\n🔄 Query expanded to: \"{metadata['expanded_query']}\"")
            
            # Show response
            print(f"\n📝 Answer:\n{'-'*40}")
            print(result.response)
            print(f"{'-'*40}")
            
            # Show sources
            if result.sources:
                print("\n📚 Sources:")
                for source in result.sources[:3]:
                    print(f"   • {source['source']} (Page {source['page']}) - Score: {source['score']:.3f}")
            
            # Ask for feedback
            feedback = input("\nRate this response (👍/👎/skip): ").strip().lower()
            if feedback in ['👍', 'good', 'yes', 'y', '+']:
                rag.submit_feedback('positive')
            elif feedback in ['👎', 'bad', 'no', 'n', '-']:
                rag.submit_feedback('negative')
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")


def query_single(question: str, top_k: int = None):
    """Run a single query."""
    rag = SelfLearningRAG()
    
    if not rag.is_ready:
        print("Building index first...")
        rag.initialize()
    
    result, metadata = rag.query(question, top_k=top_k)
    
    print(f"\n🔍 Query: {question}")
    
    if metadata.get('was_expanded'):
        print(f"🔄 Expanded to: {metadata['expanded_query']}")
    
    print(f"\n📝 Answer:\n{'-'*60}")
    print(result.response)
    print(f"{'-'*60}")
    
    print("\n📚 Sources:")
    for source in result.sources:
        print(f"   [{source['rank']}] {source['source']} (Page {source['page']}) - {source['score']:.3f}")


def check_environment():
    """Check if environment is properly configured."""
    print("\n🔍 Checking Environment...")
    print("-" * 40)
    
    results = validate_environment()
    
    all_ok = True
    for key, value in results.items():
        status = "✅" if value else "❌"
        print(f"   {status} {key}")
        if not value:
            all_ok = False
    
    if all_ok:
        print("\n✅ All checks passed!")
    else:
        print("\n⚠️  Some checks failed. See above for details.")
        print("\nTips:")
        print("  • Set GITHUB_TOKEN in .env file for LLM generation")
        print("  • Run 'pip install -r requirements.txt' to install dependencies")
        print("  • Ensure PDF files are in the Lectures folder")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="ADB Course RAG System - CLI Interface",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --build-index           Build/rebuild the search index
  python main.py --query "What is ACID?" Run a single query
  python main.py --interactive           Start interactive mode
  python main.py --check                 Check environment setup
        """
    )
    
    parser.add_argument(
        '--build-index',
        action='store_true',
        help='Build or rebuild the search index'
    )
    
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force rebuild even if index exists'
    )
    
    parser.add_argument(
        '--query', '-q',
        type=str,
        help='Run a single query'
    )
    
    parser.add_argument(
        '--top-k', '-k',
        type=int,
        default=5,
        help='Number of documents to retrieve (default: 5)'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Start interactive query mode'
    )
    
    parser.add_argument(
        '--check',
        action='store_true',
        help='Check environment setup'
    )
    
    parser.add_argument(
        '--ui',
        action='store_true',
        help='Launch Gradio UI'
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    # Handle commands
    if args.check:
        check_environment()
    elif args.build_index:
        build_index(force=args.force)
    elif args.query:
        query_single(args.query, args.top_k)
    elif args.interactive:
        query_interactive()
    elif args.ui:
        from app import main as run_ui
        run_ui()
    else:
        # Default: show help
        parser.print_help()


if __name__ == "__main__":
    main()
