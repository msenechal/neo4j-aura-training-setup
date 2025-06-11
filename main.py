import argparse
import logging
import sys
from typing import Dict, Any

from config import DEFAULT_INSTANCE_CONFIG, validate_environment
from database_manager import DatabaseManager

def setup_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('aura_setup.log')
        ]
    )

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create, clone, and manage Neo4j Aura databases for PS trainings and workshops.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
            Examples:
            # Create 5 databases
            python main.py --mode=init --nb_instances=5 --name=MS_TRAINING_AUTOMATION_TEST --memory="4GB"

            # Add 3 more instances to existing setup
            python main.py --mode=add --nb_instances=2 --name=MS_TRAINING_AUTOMATION_TEST --memory="4GB"
            
            # Delete all databases from credentials file
            python main.py --mode=delete
            
            # Delete only databases with specific base name
            python main.py --mode delete --name TRAINING
        """
    )
    
    parser.add_argument(
        "--nb_instances", type=int, default=1,
        help="Number of database instances to create (default: 1)"
    )
    parser.add_argument(
        "--name", type=str, default="TRAINING",
        help="Base name for database instances (default: TRAINING)"
    )
    parser.add_argument(
        "--output_file", type=str, default="db_credentials.json",
        help="Output file for credentials (default: db_credentials.json)"
    )
    parser.add_argument(
        "--mode", type=str, default="init", choices=["init", "add", "delete"],
        help="Mode: 'init' creates 1 instance + clones, 'add' adds clones from existing instance, 'delete' removes databases (default: init)"
    )
    
    parser.add_argument("--version", type=str, default="5", help="Neo4j version (default: 5)")
    parser.add_argument("--region", type=str, default="europe-west1", help="Cloud region (default: europe-west1)")
    parser.add_argument("--memory", type=str, default="2GB", help="Memory size (default: 2GB)")
    parser.add_argument("--type", type=str, default="enterprise-db", help="Database type (default: enterprise-db)")
    parser.add_argument("--cloud_provider", type=str, default="gcp", help="Cloud provider: gcp, aws, azure (default: gcp)")
    
    parser.add_argument("--log_level", type=str, default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level (default: INFO)")
    parser.add_argument("--force", action="store_true", help="Skip confirmation prompts (for delete mode)")
    
    return parser.parse_args()

def build_instance_config(args: argparse.Namespace) -> Dict[str, Any]:
    config = DEFAULT_INSTANCE_CONFIG.copy()
    config.update({
        "version": args.version,
        "region": args.region,
        "memory": args.memory,
        "type": args.type,
        "cloud_provider": args.cloud_provider
    })
    return config

def handle_delete_mode(args: argparse.Namespace, db_manager: DatabaseManager) -> bool:
    logger = logging.getLogger(__name__)
    
    base_name = args.name if args.name != "TRAINING" else None
    
    logger.info(f"Starting database deletion{f' for base name: {args.name}' if base_name else ''}")
    
    success = db_manager.delete_all_instances(
        credentials_file=args.output_file,
        confirm=not args.force,
        base_name=base_name
    )
    
    if success:
        logger.info("✅ All targeted databases deleted successfully!")
    else:
        logger.error("❌ Some databases could not be deleted, try again later.")
    
    return success

def main() -> None:
    args = parse_arguments()
    setup_logging(args.log_level)
    
    logger = logging.getLogger(__name__)
    
    try:
        validate_environment()
        
        db_manager = DatabaseManager()
        
        if args.mode == "delete":
            success = handle_delete_mode(args, db_manager)
            sys.exit(0 if success else 1)
        
        instance_config = build_instance_config(args)
        
        logger.info(f"Starting database setup in '{args.mode}' mode")
        logger.info(f"Target instances: {args.nb_instances}, Base name: '{args.name}'")
        logger.info(f"Instance config: {instance_config}")
        
        if args.mode == "init":
            created_dbs = db_manager.create_databases_with_clones(
                nb_instances=args.nb_instances,
                name=args.name,
                instance_config=instance_config
            )
        else:
            created_dbs = db_manager.add_cloned_instances(
                nb_instances=args.nb_instances,
                base_name=args.name,
                instance_config=instance_config,
                credentials_file=args.output_file
            )
        
        if created_dbs:
            db_manager.store_credentials(created_dbs, args.output_file)
            
            db_count = len(created_dbs)
            logger.info(f"✅ Setup completed successfully!")
            logger.info(f"Total databases: {db_count}")
            logger.info(f"Credentials stored in: {args.output_file}")
            
            if args.mode == "init":
                logger.info("Note: Cloned instances may take ~5-10 minutes to complete data loading")
        else:
            logger.error("❌ No databases were created")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
