"""
General STR Data Loader - Multi-City Compatible

This module can load STR and complaint data from any city's Google Drive folder.
Currently configured for Scottsdale data, but easily adaptable for other cities.
"""

import pandas as pd
import requests
from io import StringIO
import logging
from typing import Dict, Optional, List
import warnings
import re
warnings.filterwarnings('ignore')

class STRDataLoader:
    """General STR data loader - works with any city's Google Drive folder"""
    
    def __init__(self, city_name="Scottsdale", folder_id=None):
        """
        Initialize data loader for any city
        
        Args:
            city_name: Name of the city (for display purposes)
            folder_id: Google Drive folder ID (None to use default Scottsdale)
        """
        self.city_name = city_name
        self.folder_id = folder_id or "1FEInC_DsWaQo8XIvydEGL1e0si7wqvFg"  # Default: Your Scottsdale folder
        self.logger = logging.getLogger(__name__)
        
        # City-specific file configurations
        self.city_configs = {
            "Scottsdale": {
                "file_mappings": {
                    # STR Properties
                    'licensed_strs': {
                        'filename': 'Licensed_Short-term_Rental_Public.csv',
                        'file_id': '16-lg-5fj-dttKUgwWTbzo0wDH4lCvV-t',
                        'description': 'Licensed STR properties',
                        'category': 'properties'
                    },
                    'unlicensed_strs': {
                        'filename': 'Unlicensed_Short-term_Rentals_Public.csv',
                        'file_id': '12mlo9JtfIUfOz3CxJVCEIgVIEZKGyQ6X',
                        'description': 'Unlicensed STR properties',
                        'category': 'properties'
                    },
                    'pending_licences': {
                        'filename': 'Pending_Short-term_Rental_Licences_Public.csv',
                        'file_id': '1ybALd2DDYsdP6VgeLfnioo1kKSYt_xRR',
                        'description': 'Pending STR licence applications',
                        'category': 'properties'
                    },
                    
                    # Complaints
                    'ez_complaints': {
                        'filename': 'ScottsdaleEZ_Complaints_Public.csv',
                        'file_id': '1UDbXLlVdikJGFyVgOxLExYWFqe3ADcSj',
                        'description': 'Main complaints system',
                        'category': 'complaints'
                    },
                    'code_violations': {
                        'filename': 'Planning_and_Development_Code_Violations_Public.csv',
                        'file_id': '1vUJ-HXU1RGb9AOvn0jAaaSkiYq4ICITs',
                        'description': 'Code violations and enforcement',
                        'category': 'complaints'
                    },
                    
                    # Police Data
                    'police_incidents': {
                        'filename': 'Police_Incident_Reports_Public.csv',
                        'file_id': '1PF_cAutvvEMiAmEHzH2Qbljz73k75x0R',
                        'description': 'Police incident reports',
                        'category': 'police'
                    },
                    'police_citations': {
                        'filename': 'Police_Citations_Public.csv',
                        'file_id': '1PQW90VjQsbYXxhOlpRXKM2MRyEbmOL0N',
                        'description': 'Police citations issued',
                        'category': 'police'
                    },
                    'police_arrests': {
                        'filename': 'Police_Arrests_Public.csv',
                        'file_id': '118W8cbYAnEgzPwy1I_cVuqoHLpoMz9UG',
                        'description': 'Police arrest records',
                        'category': 'police'
                    },
                    
                    # Geographic
                    'parcels': {
                        'filename': 'Parcels_Public.csv',
                        'file_id': '19PPloUcM2FHxxQP17s4091aaLZjp4juB',
                        'description': 'Property parcel information',
                        'category': 'geographic'
                    }
                }
            }
            # Other cities can be added here:
            # "Phoenix": { "file_mappings": {...} },
            # "Austin": { "file_mappings": {...} },
        }
        
        # Get current city's file configuration
        if city_name in self.city_configs:
            self.file_configs = self.city_configs[city_name]["file_mappings"]
        else:
            self.file_configs = {}
            self.logger.warning(f"No configuration found for {city_name}")
        
        # Storage for loaded datasets
        self.datasets = {}
    
    def add_city_config(self, city_name: str, file_mappings: Dict, folder_id: str = None):
        """
        Add configuration for a new city
        
        Args:
            city_name: Name of the city
            file_mappings: Dictionary of file configurations
            folder_id: Google Drive folder ID for the city
        """
        self.city_configs[city_name] = {"file_mappings": file_mappings}
        
        if folder_id:
            # Update folder ID if provided
            self.folder_id = folder_id
            
        print(f"✅ Added configuration for {city_name}")
        print(f"📁 Folder ID: {self.folder_id}")
        print(f"📊 Datasets: {len(file_mappings)}")
    
    def setup_file_links(self, file_links: Dict[str, str]):
        """
        Set up file links manually (for cities without pre-configured file IDs)
        
        Args:
            file_links: Dictionary mapping dataset keys to Google Drive URLs
        """
        for dataset_key, url in file_links.items():
            if dataset_key not in self.file_configs:
                self.logger.warning(f"Unknown dataset key: {dataset_key}")
                continue
            
            # Extract file ID from URL
            file_id = self.extract_file_id(url)
            self.file_configs[dataset_key]['file_id'] = file_id
            
        print(f"🔗 Updated file links for {self.city_name}")
    
    def extract_file_id(self, url: str) -> str:
        """Extract file ID from Google Drive URL"""
        patterns = [
            r'/file/d/([a-zA-Z0-9-_]+)/',
            r'id=([a-zA-Z0-9-_]+)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return url.strip()  # Assume it's already just the ID
    
    def get_direct_download_url(self, file_id: str) -> str:
        """Convert Google Drive file ID to direct download URL"""
        return f"https://drive.google.com/uc?id={file_id}&export=download"
    
    def load_dataset(self, dataset_key: str) -> Optional[pd.DataFrame]:
        """
        Load a specific dataset from Google Drive
        
        Args:
            dataset_key: Key from file_configs
            
        Returns:
            DataFrame or None if loading fails
        """
        if dataset_key not in self.file_configs:
            self.logger.error(f"Unknown dataset: {dataset_key}")
            return None
        
        config = self.file_configs[dataset_key]
        file_id = config.get('file_id')
        
        if not file_id:
            self.logger.warning(f"No file ID for {dataset_key}")
            return None
        
        try:
            url = self.get_direct_download_url(file_id)
            
            self.logger.info(f"📥 Loading {config['filename']}...")
            
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            
            # Handle large files with virus scan warning
            if len(response.text) < 1000 and 'virus scan' in response.text.lower():
                url = f"https://drive.google.com/uc?id={file_id}&export=download&confirm=t"
                response = requests.get(url, timeout=120)
            
            # Load CSV
            df = pd.read_csv(StringIO(response.text), low_memory=False)
            
            self.logger.info(f"✅ {config['filename']}: {df.shape[0]:,} rows × {df.shape[1]} columns")
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load {config['filename']}: {str(e)}")
            return None
    
    def load_all_datasets(self) -> Dict[str, pd.DataFrame]:
        """
        Load all configured datasets for the current city
        
        Returns:
            Dictionary of dataset names to DataFrames
        """
        print(f"🔄 Loading all {self.city_name} STR datasets...")
        print(f"📁 Google Drive Folder: {self.folder_id}")
        print("=" * 50)
        
        self.datasets = {}
        
        for dataset_key, config in self.file_configs.items():
            df = self.load_dataset(dataset_key)
            self.datasets[dataset_key] = df
        
        # Print summary
        self._print_loading_summary()
        
        return self.datasets
    
    def _print_loading_summary(self):
        """Print summary of loaded datasets"""
        loaded_count = sum(1 for df in self.datasets.values() if df is not None)
        total_count = len(self.file_configs)
        
        print(f"\n📊 {self.city_name.upper()} LOADING SUMMARY")
        print("=" * 40)
        print(f"✅ Successfully loaded: {loaded_count}/{total_count} datasets")
        
        if loaded_count > 0:
            total_rows = 0
            total_memory = 0
            
            # Group by category
            categories = {}
            for key, df in self.datasets.items():
                if df is not None:
                    category = self.file_configs[key].get('category', 'other')
                    if category not in categories:
                        categories[category] = []
                    categories[category].append((key, df))
            
            # Print by category
            for category, datasets_list in categories.items():
                print(f"\n📁 {category.upper()}:")
                for key, df in datasets_list:
                    rows = df.shape[0]
                    memory_mb = df.memory_usage(deep=True).sum() / 1024**2
                    total_rows += rows
                    total_memory += memory_mb
                    
                    description = self.file_configs[key]['description']
                    print(f"   ✅ {description}: {rows:,} rows ({memory_mb:.1f} MB)")
            
            print(f"\n📈 TOTAL: {total_rows:,} rows, {total_memory:.1f} MB")
    
    def get_dataset_by_category(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Get datasets organized by category
        
        Returns:
            Nested dictionary with categories and datasets
        """
        categories = {}
        
        for key, df in self.datasets.items():
            if key in self.file_configs:
                category = self.file_configs[key].get('category', 'other')
                if category not in categories:
                    categories[category] = {}
                categories[category][key] = df
        
        return categories
    
    def print_city_info(self):
        """Display information about the current city configuration"""
        print(f"🏛️ {self.city_name.upper()} STR DATA CONFIGURATION")
        print("=" * 50)
        print(f"📁 Google Drive Folder: {self.folder_id}")
        print(f"📊 Available Datasets: {len(self.file_configs)}")
        
        # Group by category for display
        categories = {}
        for key, config in self.file_configs.items():
            category = config.get('category', 'other')
            if category not in categories:
                categories[category] = []
            categories[category].append(config)
        
        for category, configs in categories.items():
            print(f"\n📋 {category.upper()}:")
            for config in configs:
                status = "🔗 Ready" if config.get('file_id') else "⏳ Need setup"
                print(f"   {status} {config['filename']}")
                print(f"      └── {config['description']}")
    
    def create_sample_data_for_testing(self):
        """Create sample data when real data isn't available"""
        print(f"🔧 Creating sample data for {self.city_name} testing...")
        
        import numpy as np
        from datetime import datetime, timedelta
        
        np.random.seed(42)
        
        # Sample STR properties
        n_properties = 1000
        self.datasets['licensed_strs'] = pd.DataFrame({
            'property_id': range(1, n_properties + 1),
            'address': [f"{np.random.randint(1000, 9999)} {np.random.choice(['Main St', 'Oak Ave', 'Elm Dr'])} #{i}" 
                       for i in range(1, n_properties + 1)],
            'property_type': np.random.choice(['Single Family', 'Condo', 'Townhouse'], n_properties),
            'bedrooms': np.random.choice([2, 3, 4, 5], n_properties),
        })
        
        # Sample complaints
        n_complaints = 3000
        self.datasets['ez_complaints'] = pd.DataFrame({
            'complaint_id': range(1, n_complaints + 1),
            'address': np.random.choice(self.datasets['licensed_strs']['address'].tolist(), n_complaints),
            'complaint_date': [datetime.now() - timedelta(days=np.random.randint(0, 730)) 
                              for _ in range(n_complaints)],
            'complaint_type': np.random.choice(['Noise', 'Parking', 'Trash', 'Party'], n_complaints),
            'status': np.random.choice(['Open', 'Closed'], n_complaints, p=[0.2, 0.8]),
        })
        
        print(f"✅ Sample data created for {self.city_name} development")

# Quick usage functions for any city
def load_city_str_data(city_name="Scottsdale", folder_id=None):
    """
    Quick function to load STR data for any city
    
    Args:
        city_name: Name of the city
        folder_id: Google Drive folder ID (optional)
        
    Returns:
        Tuple of (loader, datasets)
    """
    loader = STRDataLoader(city_name=city_name, folder_id=folder_id)
    loader.print_city_info()
    
    # Try to load data, fall back to sample if needed
    try:
        datasets = loader.load_all_datasets()
        if not any(df is not None for df in datasets.values()):
            print("⚠️  No data loaded, creating sample data for testing...")
            loader.create_sample_data_for_testing()
            datasets = loader.datasets
    except Exception as e:
        print(f"❌ Error loading data: {e}")
        print("🔧 Creating sample data for testing...")
        loader.create_sample_data_for_testing()
        datasets = loader.datasets
    
    return loader, datasets

def add_new_city(city_name: str, file_links: Dict[str, str], folder_id: str = None):
    """
    Helper function to add a new city configuration
    
    Args:
        city_name: Name of the new city
        file_links: Dictionary of dataset keys to Google Drive sharing URLs
        folder_id: Google Drive folder ID
    """
    loader = STRDataLoader()
    
    # Convert file links to file mappings
    file_mappings = {}
    for key, url in file_links.items():
        file_id = loader.extract_file_id(url)
        file_mappings[key] = {
            'filename': f"{key}.csv",  # Generic filename
            'file_id': file_id,
            'description': f"{key.replace('_', ' ').title()}",
            'category': 'general'  # Can be customized
        }
    
    loader.add_city_config(city_name, file_mappings, folder_id)
    return loader

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("🏛️ Multi-City STR Data Loader")
    print("=" * 35)
    
    # Load Scottsdale data (default)
    loader, datasets = load_city_str_data("Scottsdale")
    
    print(f"\n🎯 Ready for {loader.city_name} STR nuisance analysis!")
    print(f"📊 Loaded datasets: {list(datasets.keys())}")
