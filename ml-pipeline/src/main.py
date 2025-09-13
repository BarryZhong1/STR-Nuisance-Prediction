"""
STR Nuisance Prediction System - Main Entry Point

This is the main execution script that orchestrates the entire ML pipeline:
1. Data loading and processing
2. Model training or loading
3. Prediction generation  
4. Results export for dashboard and alerts
"""

import os
import sys
import logging
import argparse
from pathlib import Path
from datetime import datetime

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.data_processing.pipeline import DataPipeline
from src.modeling.predictor import NuisancePredictor

def setup_logging(log_level="INFO"):
    """Configure logging for the application"""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('logs/str_prediction.log') if Path('logs').exists() else logging.NullHandler()
        ]
    )
    return logging.getLogger(__name__)

def main(config_path=None, mode="predict"):
    """
    Main execution function
    
    Args:
        config_path: Path to configuration file
        mode: Operation mode - 'train', 'predict', or 'full_pipeline'
    """
    logger = setup_logging()
    logger.info("🏠 STR Nuisance Prediction System Starting...")
    logger.info(f"📅 Run Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🔧 Mode: {mode}")
    
    try:
        # Initialize components
        logger.info("🔧 Initializing system components...")
        
        data_pipeline = DataPipeline(config_path or "config/template.yaml")
        predictor = NuisancePredictor()
        
        if mode in ["train", "full_pipeline"]:
            logger.info("🔄 Starting training pipeline...")
            
            # Process training data
            processed_data = data_pipeline.run()
            
            # Train model
            predictor.train(processed_data)
            
            # Save trained model
            model_save_path = "models/nuisance_predictor.joblib"
            os.makedirs("models", exist_ok=True)
            predictor.save_model(model_save_path)
            
            logger.info("✅ Training pipeline completed successfully")
        
        if mode in ["predict", "full_pipeline"]:
            logger.info("🔮 Starting prediction pipeline...")
            
            # Load model if not already trained
            if not predictor.is_trained:
                model_path = "models/nuisance_predictor.joblib"
                if Path(model_path).exists():
                    predictor.load_model(model_path)
                else:
                    logger.error("❌ No trained model found. Run training first.")
                    return
            
            # Process current data for prediction
            current_data = data_pipeline.run()
            
            # Generate predictions
            predictions = predictor.predict(current_data)
            
            # Export results
            export_predictions(predictions, logger)
            
            logger.info("✅ Prediction pipeline completed successfully")
            
        logger.info("🎉 STR Nuisance Prediction System completed successfully!")
        
    except Exception as e:
        logger.error(f"❌ System failed: {str(e)}")
        logger.exception("Full error details:")
        sys.exit(1)

def export_predictions(predictions, logger):
    """
    Export predictions for dashboard and alerts
    
    Args:
        predictions: DataFrame with predictions and risk scores
        logger: Logger instance
    """
    logger.info("📊 Exporting predictions...")
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Export full predictions for dashboard
    dashboard_file = output_dir / f"predictions_dashboard_{datetime.now().strftime('%Y%m%d')}.csv"
    predictions.to_csv(dashboard_file, index=False)
    logger.info(f"📈 Dashboard data exported to: {dashboard_file}")
    
    # Export high-risk properties for alerts
    high_risk = predictions[predictions['risk_level'] == 'High']
    if not high_risk.empty:
        alerts_file = output_dir / f"high_risk_alerts_{datetime.now().strftime('%Y%m%d')}.csv"
        high_risk.to_csv(alerts_file, index=False)
        logger.info(f"🚨 High-risk alerts exported to: {alerts_file}")
        logger.info(f"🔴 Found {len(high_risk)} high-risk properties")
    else:
        logger.info("✅ No high-risk properties identified")
    
    # Print summary statistics
    risk_counts = predictions['risk_level'].value_counts()
    logger.info("📊 Risk Level Summary:")
    for level, count in risk_counts.items():
        logger.info(f"   {level}: {count} properties")

if __name__ == "__main__":
    # Command line argument parsing
    parser = argparse.ArgumentParser(description="STR Nuisance Prediction System")
    parser.add_argument("--config", help="Path to configuration file")
    parser.add_argument("--mode", choices=["train", "predict", "full_pipeline"], 
                       default="predict", help="Operation mode")
    parser.add_argument("--log-level", default="INFO", help="Logging level")
    
    args = parser.parse_args()
    
    # Run main function
    main(config_path=args.config, mode=args.mode)
