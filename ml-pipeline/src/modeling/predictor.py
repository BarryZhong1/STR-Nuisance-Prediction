"""
Machine learning models for STR nuisance prediction
"""

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import joblib
import logging
from pathlib import Path

class NuisancePredictor:
    """ML model for predicting STR nuisance probability"""
    
    def __init__(self, model_type="random_forest"):
        """
        Initialize predictor
        Args:
            model_type: Type of ML model to use
        """
        self.model_type = model_type
        self.model = None
        self.feature_columns = None
        self.is_trained = False
        self.logger = logging.getLogger(__name__)
    
    def prepare_features(self, df):
        """
        Prepare features for model training/prediction
        Args:
            df: Input dataframe
        Returns:
            Feature matrix (X) and target vector (y) if available
        """
        # TODO: Implement based on your feature engineering
        # This should match your Colab analysis
        
        # Example feature preparation (customize this)
        feature_cols = [
            'complaint_count_last_year',
            'property_age',
            'neighborhood_risk_score',
            # Add your actual features here
        ]
        
        X = df[feature_cols] if all(col in df.columns for col in feature_cols) else pd.DataFrame()
        y = df['is_nuisance'] if 'is_nuisance' in df.columns else None
        
        return X, y
    
    def train(self, df):
        """
        Train the nuisance prediction model
        Args:
            df: Training dataframe with features and target
        """
        self.logger.info("🤖 Training nuisance prediction model...")
        
        # Prepare features
        X, y = self.prepare_features(df)
        
        if X.empty or y is None:
            raise ValueError("No valid features or target found for training")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=y
        )
        
        # Initialize model
        if self.model_type == "random_forest":
            self.model = RandomForestClassifier(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
        
        # Train model
        self.model.fit(X_train, y_train)
        self.feature_columns = X.columns.tolist()
        self.is_trained = True
        
        # Evaluate on test set
        y_pred = self.model.predict(X_test)
        self.logger.info("📊 Model Performance:")
        self.logger.info(f"\n{classification_report(y_test, y_pred)}")
        
        self.logger.info("✅ Model training completed")
        return self.model
    
    def predict(self, df):
        """
        Generate nuisance probability predictions
        Args:
            df: Dataframe with features for prediction
        Returns:
            DataFrame with predictions and probabilities
        """
        if not self.is_trained:
            raise ValueError("Model must be trained before making predictions")
        
        self.logger.info("🔮 Generating nuisance predictions...")
        
        # Prepare features
        X, _ = self.prepare_features(df)
        
        if X.empty:
            raise ValueError("No valid features found for prediction")
        
        # Generate predictions
        predictions = self.model.predict(X)
        probabilities = self.model.predict_proba(X)[:, 1]  # Probability of nuisance
        
        # Create results dataframe
        results = df.copy()
        results['nuisance_prediction'] = predictions
        results['nuisance_probability'] = probabilities
        results['risk_level'] = self.categorize_risk(probabilities)
        
        self.logger.info("✅ Predictions generated successfully")
        return results
    
    def categorize_risk(self, probabilities):
        """
        Categorize probabilities into risk levels
        Args:
            probabilities: Array of nuisance probabilities
        Returns:
            Array of risk categories
        """
        risk_levels = []
        for prob in probabilities:
            if prob < 0.3:
                risk_levels.append('Low')
            elif prob < 0.7:
                risk_levels.append('Medium')
            else:
                risk_levels.append('High')
        
        return risk_levels
    
    def save_model(self, filepath):
        """Save trained model to file"""
        if not self.is_trained:
            raise ValueError("Cannot save untrained model")
        
        model_data = {
            'model': self.model,
            'feature_columns': self.feature_columns,
            'model_type': self.model_type
        }
        
        joblib.dump(model_data, filepath)
        self.logger.info(f"💾 Model saved to {filepath}")
    
    def load_model(self, filepath):
        """Load trained model from file"""
        model_data = joblib.load(filepath)
        self.model = model_data['model']
        self.feature_columns = model_data['feature_columns'] 
        self.model_type = model_data['model_type']
        self.is_trained = True
        
        self.logger.info(f"📂 Model loaded from {filepath}")

if __name__ == "__main__":
    # Test the predictor
    predictor = NuisancePredictor()
    print("Nuisance predictor initialized successfully")
