#!/usr/bin/env python3

"""
Analysis Results Visualizer - Generate graphs and tables from CC3D object analysis results
"""

import json
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
from collections import Counter, defaultdict
import argparse

class AnalysisVisualizer:
    """Create visualizations from analysis results"""
    
    def __init__(self, results_dir: Path = Path("analysis_results")):
        self.results_dir = results_dir
        self.data = None
        self.summary_stats = None
        
    def load_all_results(self) -> pd.DataFrame:
        """Load all analysis results into a comprehensive DataFrame"""
        
        all_data = []
        
        # Find all JSON result files
        json_files = list(self.results_dir.glob("*_object_analysis.json"))
        
        print(f"📊 Loading {len(json_files)} analysis result files...")
        
        for json_file in json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                
                # Extract paper info from filename
                filename = json_file.stem
                parts = filename.replace('_object_analysis', '').split('_')
                paper_id = parts[1] if len(parts) > 1 else "unknown"
                paper_name = '_'.join(parts[2:-1]) if len(parts) > 3 else "unknown"
                timestamp = parts[-1] if len(parts) > 0 else "unknown"
                
                # Extract summary metrics
                summary = data.get('summary', {})
                
                # Count API styles
                api_styles = summary.get('api_styles', {})
                total_runs = sum(api_styles.values()) if api_styles else 0
                
                # Calculate API consistency (what fraction is the most common API?)
                if api_styles:
                    max_api_count = max(api_styles.values())
                    api_consistency = max_api_count / total_runs if total_runs > 0 else 0
                    dominant_api = max(api_styles.keys(), key=api_styles.get)
                else:
                    api_consistency = 0
                    dominant_api = "unknown"
                
                # Extract run-level data
                run_info = data.get('run_info', [])
                
                # Aggregate data for this paper
                paper_data = {
                    'paper_id': int(paper_id) if paper_id.isdigit() else 0,
                    'paper_name': paper_name,
                    'timestamp': timestamp,
                    'total_runs': total_runs,
                    'files_analyzed': data.get('files_analyzed', 0),
                    
                    # API Statistics
                    'dominant_api': dominant_api,
                    'api_consistency': api_consistency,
                    'modern_api_count': api_styles.get('modern', 0),
                    'legacy_api_count': api_styles.get('legacy', 0),
                    'mixed_api_count': api_styles.get('mixed', 0),
                    'unknown_api_count': api_styles.get('unknown', 0),
                    
                    # Averages
                    'avg_classes': summary.get('avg_classes', 0),
                    'avg_cell_types': summary.get('avg_cell_types', 0),
                    'avg_parameters': summary.get('avg_parameters', 0),
                    'avg_behaviors': summary.get('avg_behaviors', 0),
                    'syntax_error_runs': summary.get('syntax_error_runs', 0),
                    
                    # Derived metrics
                    'syntax_error_rate': summary.get('syntax_error_runs', 0) / total_runs if total_runs > 0 else 0,
                    'has_mixed_apis': api_styles.get('mixed', 0) > 0,
                    'is_consistent': api_consistency > 0.8,  # 80% threshold for consistency
                }
                
                # Add variance calculations if we have run-level data
                if run_info:
                    classes_values = [r.get('num_classes', 0) for r in run_info]
                    cell_types_values = [r.get('num_cell_types', 0) for r in run_info]
                    parameters_values = [r.get('num_parameters', 0) for r in run_info]
                    behaviors_values = [r.get('num_behaviors', 0) for r in run_info]
                    
                    paper_data.update({
                        'classes_variance': np.var(classes_values) if len(classes_values) > 1 else 0,
                        'cell_types_variance': np.var(cell_types_values) if len(cell_types_values) > 1 else 0,
                        'parameters_variance': np.var(parameters_values) if len(parameters_values) > 1 else 0,
                        'behaviors_variance': np.var(behaviors_values) if len(behaviors_values) > 1 else 0,
                    })
                
                all_data.append(paper_data)
                
            except Exception as e:
                print(f"❌ Error loading {json_file}: {e}")
                continue
        
        if not all_data:
            raise ValueError("No valid analysis results found!")
        
        self.data = pd.DataFrame(all_data).sort_values('paper_id')
        print(f"✅ Loaded data for {len(self.data)} papers")
        
        return self.data
    
    def calculate_summary_stats(self):
        """Calculate overall summary statistics"""
        if self.data is None:
            self.load_all_results()
        
        self.summary_stats = {
            'total_papers': len(self.data),
            'total_runs': self.data['total_runs'].sum(),
            'avg_runs_per_paper': self.data['total_runs'].mean(),
            
            # API Distribution
            'papers_with_consistent_apis': self.data['is_consistent'].sum(),
            'papers_with_mixed_apis': self.data['has_mixed_apis'].sum(),
            'consistency_rate': self.data['is_consistent'].mean(),
            
            # Dominant API types
            'modern_api_papers': (self.data['dominant_api'] == 'modern').sum(),
            'legacy_api_papers': (self.data['dominant_api'] == 'legacy').sum(),
            'mixed_api_papers': (self.data['dominant_api'] == 'mixed').sum(),
            'unknown_api_papers': (self.data['dominant_api'] == 'unknown').sum(),
            
            # Quality metrics
            'avg_syntax_error_rate': self.data['syntax_error_rate'].mean(),
            'papers_with_syntax_errors': (self.data['syntax_error_runs'] > 0).sum(),
            
            # Complexity metrics
            'avg_classes_across_all': self.data['avg_classes'].mean(),
            'avg_cell_types_across_all': self.data['avg_cell_types'].mean(),
            'avg_parameters_across_all': self.data['avg_parameters'].mean(),
            'avg_behaviors_across_all': self.data['avg_behaviors'].mean(),
        }
        
        return self.summary_stats
    
    def create_api_consistency_chart(self, save_path: Path = None):
        """Create a chart showing API consistency across papers"""
        if self.data is None:
            self.load_all_results()
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Chart 1: API Consistency Distribution
        consistency_bins = [0, 0.2, 0.4, 0.6, 0.8, 1.0]
        consistency_labels = ['0-20%', '20-40%', '40-60%', '60-80%', '80-100%']
        
        binned_data = pd.cut(self.data['api_consistency'], bins=consistency_bins, labels=consistency_labels, include_lowest=True)
        counts = binned_data.value_counts().sort_index()
        
        colors = ['#d32f2f', '#f57c00', '#fbc02d', '#689f38', '#388e3c']
        ax1.bar(range(len(counts)), counts.values, color=colors, alpha=0.8)
        ax1.set_xticks(range(len(counts)))
        ax1.set_xticklabels(counts.index, rotation=45)
        ax1.set_ylabel('Number of Papers')
        ax1.set_title('API Consistency Distribution\n(% of runs with same API)')
        ax1.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for i, v in enumerate(counts.values):
            ax1.text(i, v + 0.1, str(v), ha='center', va='bottom', fontweight='bold')
        
        # Chart 2: Dominant API Types
        api_counts = self.data['dominant_api'].value_counts()
        colors_api = {'modern': '#2196f3', 'legacy': '#ff9800', 'mixed': '#f44336', 'unknown': '#9e9e9e'}
        
        bars = ax2.bar(api_counts.index, api_counts.values, 
                      color=[colors_api.get(api, '#9e9e9e') for api in api_counts.index],
                      alpha=0.8)
        ax2.set_ylabel('Number of Papers')
        ax2.set_title('Dominant API Types Across Papers')
        ax2.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bar, value in zip(bars, api_counts.values):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                    f'{value}\n({value/len(self.data)*100:.1f}%)',
                    ha='center', va='bottom', fontweight='bold')
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 API consistency chart saved to: {save_path}")
        
        return fig
    
    def create_complexity_analysis(self, save_path: Path = None):
        """Create charts showing code complexity metrics"""
        if self.data is None:
            self.load_all_results()
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 12))
        
        # Chart 1: Average Classes per Paper
        ax1.hist(self.data['avg_classes'], bins=15, alpha=0.7, color='#2196f3', edgecolor='black')
        ax1.set_xlabel('Average Classes per Run')
        ax1.set_ylabel('Number of Papers')
        ax1.set_title('Distribution of Average Classes')
        ax1.grid(axis='y', alpha=0.3)
        ax1.axvline(self.data['avg_classes'].mean(), color='red', linestyle='--', 
                   label=f'Mean: {self.data["avg_classes"].mean():.1f}')
        ax1.legend()
        
        # Chart 2: Average Cell Types per Paper
        ax2.hist(self.data['avg_cell_types'], bins=15, alpha=0.7, color='#4caf50', edgecolor='black')
        ax2.set_xlabel('Average Cell Types per Run')
        ax2.set_ylabel('Number of Papers')
        ax2.set_title('Distribution of Average Cell Types')
        ax2.grid(axis='y', alpha=0.3)
        ax2.axvline(self.data['avg_cell_types'].mean(), color='red', linestyle='--', 
                   label=f'Mean: {self.data["avg_cell_types"].mean():.1f}')
        ax2.legend()
        
        # Chart 3: Average Parameters per Paper
        ax3.hist(self.data['avg_parameters'], bins=15, alpha=0.7, color='#ff9800', edgecolor='black')
        ax3.set_xlabel('Average Parameters per Run')
        ax3.set_ylabel('Number of Papers')
        ax3.set_title('Distribution of Average Parameters')
        ax3.grid(axis='y', alpha=0.3)
        ax3.axvline(self.data['avg_parameters'].mean(), color='red', linestyle='--', 
                   label=f'Mean: {self.data["avg_parameters"].mean():.1f}')
        ax3.legend()
        
        # Chart 4: Syntax Error Rate
        ax4.hist(self.data['syntax_error_rate'], bins=10, alpha=0.7, color='#f44336', edgecolor='black')
        ax4.set_xlabel('Syntax Error Rate')
        ax4.set_ylabel('Number of Papers')
        ax4.set_title('Distribution of Syntax Error Rates')
        ax4.grid(axis='y', alpha=0.3)
        ax4.axvline(self.data['syntax_error_rate'].mean(), color='darkred', linestyle='--', 
                   label=f'Mean: {self.data["syntax_error_rate"].mean():.1%}')
        ax4.legend()
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Complexity analysis saved to: {save_path}")
        
        return fig
    
    def create_correlation_heatmap(self, save_path: Path = None):
        """Create a correlation heatmap of key metrics"""
        if self.data is None:
            self.load_all_results()
        
        # Select numerical columns for correlation
        corr_columns = [
            'api_consistency', 'avg_classes', 'avg_cell_types', 
            'avg_parameters', 'avg_behaviors', 'syntax_error_rate'
        ]
        
        correlation_data = self.data[corr_columns].corr()
        
        plt.figure(figsize=(10, 8))
        mask = np.triu(np.ones_like(correlation_data, dtype=bool))
        
        sns.heatmap(correlation_data, mask=mask, annot=True, cmap='RdBu_r', center=0,
                   square=True, fmt='.2f', cbar_kws={"shrink": .8})
        
        plt.title('Correlation Matrix of Analysis Metrics')
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            print(f"📊 Correlation heatmap saved to: {save_path}")
        
        return plt.gcf()
    
    def create_summary_table(self) -> pd.DataFrame:
        """Create a comprehensive summary table"""
        if self.data is None:
            self.load_all_results()
        
        if self.summary_stats is None:
            self.calculate_summary_stats()
        
        # Create paper-level summary
        summary_table = self.data[[
            'paper_id', 'paper_name', 'total_runs', 'dominant_api', 'api_consistency',
            'avg_classes', 'avg_cell_types', 'avg_parameters', 'syntax_error_rate',
            'is_consistent', 'has_mixed_apis'
        ]].copy()
        
        # Add descriptive columns
        summary_table['consistency_grade'] = summary_table['api_consistency'].apply(
            lambda x: 'Excellent' if x >= 0.9 else
                     'Good' if x >= 0.8 else
                     'Fair' if x >= 0.6 else
                     'Poor' if x >= 0.4 else 'Very Poor'
        )
        
        summary_table['quality_issues'] = summary_table.apply(
            lambda row: ', '.join([
                issue for issue, condition in [
                    ('Mixed APIs', row['has_mixed_apis']),
                    ('Syntax Errors', row['syntax_error_rate'] > 0),
                    ('Low Consistency', row['api_consistency'] < 0.8)
                ] if condition
            ]) or 'None', axis=1
        )
        
        # Round numerical columns
        numerical_cols = ['api_consistency', 'avg_classes', 'avg_cell_types', 'avg_parameters', 'syntax_error_rate']
        for col in numerical_cols:
            summary_table[col] = summary_table[col].round(2)
        
        return summary_table
    
    def save_summary_table(self, output_path: Path = None):
        """Save the summary table to CSV and HTML"""
        summary_table = self.create_summary_table()
        
        if output_path is None:
            output_path = Path("analysis_summary")
        
        # Save as CSV
        csv_path = output_path.with_suffix('.csv')
        summary_table.to_csv(csv_path, index=False)
        print(f"📊 Summary table saved to: {csv_path}")
        
        # Save as HTML with styling
        html_path = output_path.with_suffix('.html')
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>CC3D Analysis Summary</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                .excellent {{ background-color: #c8e6c9; }}
                .good {{ background-color: #dcedc8; }}
                .fair {{ background-color: #fff9c4; }}
                .poor {{ background-color: #ffcdd2; }}
                .very-poor {{ background-color: #ffcdd2; }}
            </style>
        </head>
        <body>
            <h1>CC3D Object Analysis Summary</h1>
            <p>Generated from {len(summary_table)} papers with {self.summary_stats['total_runs']} total runs</p>
            {summary_table.to_html(index=False, escape=False, classes='table')}
        </body>
        </html>
        """
        
        with open(html_path, 'w') as f:
            f.write(html_content)
        print(f"📊 HTML summary saved to: {html_path}")
        
        return csv_path, html_path
    
    def generate_basic_analysis(self, output_dir: Path = Path("visualizations")):
        """Generate basic analysis without complex dependencies"""
        output_dir.mkdir(exist_ok=True)
        
        print("🎨 Generating basic analysis...")
        
        # Load data
        self.load_all_results()
        
        # Generate summary table
        self.save_summary_table(output_dir / "summary_table.csv")
        
        # Create basic statistics text file
        stats_file = output_dir / "statistics.txt"
        
        # Calculate basic statistics
        total_papers = len(self.data)
        total_runs = self.data['total_runs'].sum()
        avg_runs_per_paper = self.data['total_runs'].mean()
        
        # API distribution
        api_counts = self.data['dominant_api'].value_counts()
        
        # Consistency analysis
        consistent_papers = (self.data['api_consistency'] > 0.8).sum()
        mixed_api_papers = self.data['has_mixed_apis'].sum()
        
        # Quality metrics
        avg_syntax_error_rate = self.data['syntax_error_rate'].mean()
        papers_with_errors = (self.data['syntax_error_runs'] > 0).sum()
        
        stats_content = f"""CC3D Object Analysis Results Summary
Generated from {total_papers} papers with {total_runs} total runs

OVERALL STATISTICS:
- Total Papers Analyzed: {total_papers}
- Total Runs: {total_runs}
- Average Runs per Paper: {avg_runs_per_paper:.1f}

API CONSISTENCY:
- Papers with Consistent APIs (>80%): {consistent_papers} ({consistent_papers/total_papers:.1%})
- Papers with Mixed APIs: {mixed_api_papers} ({mixed_api_papers/total_papers:.1%})

API DISTRIBUTION:
"""
        
        for api_type, count in api_counts.items():
            stats_content += f"- {api_type.capitalize()} API: {count} papers ({count/total_papers:.1%})\n"
        
        stats_content += f"""
QUALITY METRICS:
- Average Syntax Error Rate: {avg_syntax_error_rate:.1%}
- Papers with Syntax Errors: {papers_with_errors} ({papers_with_errors/total_papers:.1%})

COMPLEXITY METRICS:
- Average Classes per Run: {self.data['avg_classes'].mean():.1f}
- Average Cell Types per Run: {self.data['avg_cell_types'].mean():.1f}
- Average Parameters per Run: {self.data['avg_parameters'].mean():.1f}
- Average Behaviors per Run: {self.data['avg_behaviors'].mean():.1f}

TOP ISSUES:
"""
        
        # Find papers with most issues
        problematic_papers = self.data[
            (self.data['api_consistency'] < 0.8) | 
            (self.data['has_mixed_apis']) | 
            (self.data['syntax_error_rate'] > 0)
        ].sort_values('api_consistency')
        
        for _, paper in problematic_papers.head(10).iterrows():
            issues = []
            if paper['api_consistency'] < 0.8:
                issues.append(f"Low API consistency ({paper['api_consistency']:.1%})")
            if paper['has_mixed_apis']:
                issues.append("Mixed APIs")
            if paper['syntax_error_rate'] > 0:
                issues.append(f"Syntax errors ({paper['syntax_error_rate']:.1%})")
            
            stats_content += f"- Paper {paper['paper_id']:02d} ({paper['paper_name']}): {', '.join(issues)}\n"
        
        with open(stats_file, 'w') as f:
            f.write(stats_content)
        
        print(f"📊 Statistics saved to: {stats_file}")
        print(f"\n{stats_content}")
        
        return output_dir

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="Visualize CC3D Analysis Results")
    parser.add_argument("--results-dir", "-r", type=str, default="analysis_results",
                       help="Directory containing analysis results")
    parser.add_argument("--output-dir", "-o", type=str, default="visualizations",
                       help="Output directory for visualizations")
    
    args = parser.parse_args()
    
    try:
        # Create visualizer
        visualizer = AnalysisVisualizer(Path(args.results_dir))
        
        # Generate basic analysis
        output_dir = visualizer.generate_basic_analysis(Path(args.output_dir))
        
        print(f"\n✅ Analysis complete! Check {output_dir} for results.")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 