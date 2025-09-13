"""
Simple Google Drive Data Loader for STR Project

This loader works with your specific Google Drive folder by trying different approaches
to load the CSV files you have uploaded.
"""

import pandas as pd
import requests
from io import StringIO
import logging
from typing import Dict, Optional, List
import time

class STRDataLoader:
    """Simple data loader for STR datasets from Google Drive folder"""
    
    def __init__(self, folder_id="1FEInC_DsWaQo8XIvydEGL1e0si7wqvFg"):
        """
        Initialize with your Google Drive folder ID
        
        Args:
            folder_id: Your Google Drive folder ID
        """
        self.folder_id = folder_id
        self.logger = logging.getLogger(__name__)
        
        # We'll populate this with file IDs you provide
        self.datasets = {}
    
    def load_from_file_id(self, file_id: str, dataset_name: str) -> Optional[pd.DataFrame]:
        """
        Load a specific file by its Google Drive file ID
        
        Args:
            file_id: Google Drive file ID  
            dataset_name: Name for logging
            
        Returns:
            DataFrame or None
        """
        try:
            # Direct download URL
            url = f"https://drive.google.com/uc?id={file_id}&export=download"
            
            self.logger.info(f"📥 Loading {dataset_name}...")
            
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # Handle large files that trigger virus scan
            if 'virus scan warning' in response.text.lower() or len(response.text) < 1000:
                # Try alternative download method
                url = f"https://drive.google.com/uc?id={file_id}&export=download&confirm=t"
                response = requests.get(url, timeout=60)
            
            # Load CSV
            df = pd.read_csv(StringIO(response.text))
            
            self.logger.info(f"✅ {dataset_name}: {df.shape[0]:,} rows × {df.shape[1]} columns")
            
            return df
            
        except Exception as e:
            self.logger.error(f"❌ Failed to load {dataset_name}: {str(e)}")
            return None
    
    def setup_with_file_urls(self, file_urls: Dict[str, str]):
        """
        Set up the loader with Google Drive file URLs
        
        Args:
            file_urls: Dictionary mapping dataset names to Google Drive sharing URLs
        """
        for name, url in file_urls.items():
            # Extract file ID from sharing URL
            if '/file/d/' in url:
                file_id = url.split('/file/d/')[1].split('/')[0]
            elif '?id=' in url:
                file_id = url.split('?id=')[1].split('&')[0]
            else:
                file_id = url  # Assume it's already just the ID
            
            # Load the dataset
            df = self.load_from_file_id(file_id, name)
            if df is not None:
                self.datasets[name] = df
    
    def get_folder_contents_instruction(self):
        """
        Print instructions for getting individual file links from the folder
        """
        print("📁 TO LOAD YOUR DATA FROM GOOGLE DRIVE FOLDER:")
        print("=" * 60)
        print(f"1. Go to your folder: https://drive.google.com/drive/folders/{self.folder_id}")
        print("2. For EACH CSV file in the folder:")
        print("   • Right-click on the file")
        print("   • Select 'Get link'") 
        print("   • Make sure it's set to 'Anyone with the link can view'")
        print("   • Copy the link")
        print("3. Then use this code:")
        print()
        print("file_links = {")
        print("    'complaints': 'https://drive.google.com/file/d/YOUR_COMPLAINTS_FILE_ID/view',")
        print("    'properties': 'https://drive.google.com/file/d/YOUR_PROPERTIES_FILE_ID/view',")
        print("    'violations': 'https://drive.google.com/file/d/YOUR_VIOLATIONS_FILE_ID/view',")
        print("}")
        print("loader.setup_with_file_urls(file_links)")
        print()
    
    def load_sample_data_if_no_files(self):
        """
        Create sample data for testing if no real files are loaded
        """
        if len(self.datasets) == 0:
            self.logger.info("📝 No data files loaded, creating sample data for testing...")
            
            # Create sample properties data
            import numpy as np
            from datetime import datetime, timedelta
            
            np.random.seed(42)
            n_properties = 1000
            
            self.datasets['properties'] = pd.DataFrame({
                'property_id': range(1, n_properties + 1),
                'address': [f"{np.random.randint(100, 9999)} {np.random.choice(['Main St', 'Oak Ave', 'Pine Dr'])} #{i}" 
                           for i in range(1, n_properties + 1)],
                'property_type': np.random.choice(['Single Family', 'Condo', 'Townhouse'], n_properties),
                'bedrooms': np.random.choice([1, 2, 3, 4, 5], n_properties),
                'permit_date': [datetime.now() - timedelta(days=np.random.randint(0, 1095)) 
                               for _ in range(n_properties)],
                'owner_type': np.random.choice(['Individual', 'LLC', 'Corporation'], n_properties),
            })
            
            # Create sample complaints data
            n_complaints = 3000
            self.datasets['complaints'] = pd.DataFrame({
                'complaint_id': range(1, n_complaints + 1),
                'property_id': np.random.choice(range(1, n_properties + 1), n_complaints),
                'complaint_date': [datetime.now() - timedelta(days=np.random.randint(0, 730)) 
                                  for _ in range(n_complaints)],
                'complaint_type': np.random.choice(['Noise', 'Parking', 'Trash', 'Party'], n_complaints),
                'status': np.random.choice(['Open', 'Closed'], n_complaints, p=[0.2, 0.8]),
            })
            
            self.logger.info("✅ Sample data created for development")
    
    def get_all_datasets(self) -> Dict[str, pd.DataFrame]:
        """
        Get all loaded datasets
        
        Returns:
            Dictionary of dataset name to DataFrame
        """
        if len(self.datasets) == 0:
            self.get_folder_contents_instruction()
            self.load_sample_data_if_no_files()
        
        return self.datasets
    
    def print_summary(self):
        """Print summary of all loaded datasets"""
        print("\n📊 LOADED DATASETS SUMMARY")
        print("=" * 40)
        
        if len(self.datasets) == 0:
            print("❌ No datasets loaded")
            return
        
        total_rows = 0
        for name, df in self.datasets.items():
            rows, cols = df.shape
            memory_mb = df.memory_usage(deep=True).sum() / 1024**2
            missing = df.isnull().sum().sum()
            
            print(f"📋 {name.title()}:")
            print(f"   Rows: {rows:,}")
            print(f"   Columns: {cols}")
            print(f"   Memory: {memory_mb:.1f} MB")
            print(f"   Missing values: {missing:,}")
            print(f"   Columns: {list(df.columns)}")
            print()
            
            total_rows += rows
        
        print(f"📊 Total: {len(self.datasets)} datasets, {total_rows:,} total rows")

# Quick usage functions
def quick_load_str_data():
    """Quick function to load STR data with instructions"""
    loader = STRDataLoader()
    datasets = loader.get_all_datasets()
    loader.print_summary()
    return datasets

def load_with_file_links(file_links: Dict[str, str]):
    """Load data with provided Google Drive file links"""
    loader = STRDataLoader()
    loader.setup_with_file_urls(file_links)
    return loader.get_all_datasets()

# Example usage
if __name__ == "__main__":
    # Set up logging
    logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
    
    print("🏠 STR Data Loader")
    print("=" * 30)
    
    # Load data
    datasets = quick_load_str_data()
    
    # Show what we loaded
    for name, df in datasets.items():
        if df is not None:
            print(f"\n{name.upper()} preview:")
            print(df.head(2))
