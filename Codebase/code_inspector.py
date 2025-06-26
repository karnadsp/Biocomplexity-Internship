#!/usr/bin/env python3

"""
Code Inspector - Extract and display problematic code sections in human-readable format
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
import argparse

@dataclass
class CodeIssue:
    """Represents a code issue with context"""
    issue_type: str
    severity: str  # "high", "medium", "low"
    description: str
    code_snippet: str
    line_numbers: Optional[Tuple[int, int]] = None
    suggestions: List[str] = None

class CodeInspector:
    """Inspect and extract problematic code sections"""
    
    def __init__(self, results_dir: Path = Path("analysis_results")):
        self.results_dir = results_dir
        self.modern_api_patterns = [
            r'from cc3d\.core\.PyCoreSpecs import',
            r'from steppables\.SteppableBasePy import',
            r'steppables\.SteppableBasePy',
            r'cc3d\.core\.',
        ]
        
        self.legacy_api_patterns = [
            r'from pybind\.core import',
            r'from PySteppables import',
            r'addCellType\(',
            r'cellField\.',
            r'PySteppables',
        ]
        
        self.syntax_error_patterns = [
            r'def\s+\w+\s*\([^)]*\)\s*$',  # Function without colon
            r'if\s+[^:]+$',  # If statement without colon
            r'for\s+[^:]+$',  # For statement without colon
            r'while\s+[^:]+$',  # While statement without colon
            r'class\s+\w+\s*\([^)]*\)\s*$',  # Class without colon
        ]
    
    def extract_code_from_json(self, json_file: Path) -> Tuple[str, Dict]:
        """Extract Python code and metadata from experiment JSON"""
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Get the final code
        code_content = None
        if 'metadata' in data and 'cc3d_file_creation' in data['metadata']:
            code_content = data['metadata']['cc3d_file_creation']['python_code']
        elif 'llm_responses' in data and len(data['llm_responses']) > 1:
            response = data['llm_responses'][1]['response']
            if '```python' in response:
                code_content = response.split('```python')[1].split('```')[0].strip()
            elif '```' in response:
                code_content = response.split('```')[1].split('```')[0].strip()
        
        return code_content, data
    
    def analyze_api_mixing(self, code: str) -> List[CodeIssue]:
        """Detect mixed API usage"""
        issues = []
        lines = code.split('\n')
        
        modern_matches = []
        legacy_matches = []
        
        for i, line in enumerate(lines, 1):
            # Check for modern API patterns
            for pattern in self.modern_api_patterns:
                if re.search(pattern, line):
                    modern_matches.append((i, line.strip(), pattern))
            
            # Check for legacy API patterns  
            for pattern in self.legacy_api_patterns:
                if re.search(pattern, line):
                    legacy_matches.append((i, line.strip(), pattern))
        
        # If we have both modern and legacy, it's mixed
        if modern_matches and legacy_matches:
            # Create snippet showing the mixing
            all_matches = sorted(modern_matches + legacy_matches, key=lambda x: x[0])
            
            snippet_lines = []
            snippet_lines.append("# MIXED API DETECTED - This code won't work properly!")
            snippet_lines.append("")
            
            for line_num, line_content, pattern in all_matches:
                api_type = "MODERN" if pattern in self.modern_api_patterns else "LEGACY"
                snippet_lines.append(f"# Line {line_num} - {api_type} API:")
                snippet_lines.append(line_content)
                snippet_lines.append("")
            
            issue = CodeIssue(
                issue_type="Mixed API",
                severity="high",
                description=f"Code mixes {len(modern_matches)} modern API calls with {len(legacy_matches)} legacy API calls",
                code_snippet='\n'.join(snippet_lines),
                line_numbers=(min(all_matches, key=lambda x: x[0])[0], 
                            max(all_matches, key=lambda x: x[0])[0]),
                suggestions=[
                    "Choose either modern OR legacy API, not both",
                    "Modern API: Use 'from cc3d.core.PyCoreSpecs import *'",
                    "Legacy API: Use 'from pybind.core import *'",
                    "Modern is recommended for new code"
                ]
            )
            issues.append(issue)
        
        return issues
    
    def analyze_syntax_errors(self, code: str) -> List[CodeIssue]:
        """Detect common syntax errors"""
        issues = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            if not line_stripped:
                continue
                
            # Check for missing colons
            for pattern in self.syntax_error_patterns:
                if re.match(pattern, line_stripped):
                    # Look ahead to see if next non-empty line is indented (which would indicate missing colon)
                    next_lines = lines[i:i+3]  # Look at next few lines
                    has_indented_next = any(line.startswith('    ') or line.startswith('\t') 
                                          for line in next_lines if line.strip())
                    
                    if has_indented_next:
                        snippet = f"# Line {i} - Missing colon:\n{line_stripped}\n# Should be:\n{line_stripped}:"
                        
                        issue = CodeIssue(
                            issue_type="Syntax Error",
                            severity="high", 
                            description=f"Missing colon at end of line {i}",
                            code_snippet=snippet,
                            line_numbers=(i, i),
                            suggestions=["Add ':' at the end of the line"]
                        )
                        issues.append(issue)
        
        return issues
    
    def analyze_inconsistent_imports(self, code: str) -> List[CodeIssue]:
        """Detect inconsistent or redundant imports"""
        issues = []
        lines = code.split('\n')
        
        import_lines = []
        for i, line in enumerate(lines, 1):
            if line.strip().startswith(('import ', 'from ')):
                import_lines.append((i, line.strip()))
        
        if len(import_lines) > 10:  # Too many imports might indicate confusion
            snippet_lines = ["# EXCESSIVE IMPORTS - May indicate AI confusion:"]
            snippet_lines.append("")
            for line_num, import_line in import_lines:
                snippet_lines.append(f"# Line {line_num}:")
                snippet_lines.append(import_line)
            
            issue = CodeIssue(
                issue_type="Import Issues",
                severity="medium",
                description=f"Excessive imports ({len(import_lines)} import statements)",
                code_snippet='\n'.join(snippet_lines),
                suggestions=[
                    "Remove unnecessary imports",
                    "Group related imports together",
                    "Use 'from module import *' sparingly"
                ]
            )
            issues.append(issue)
        
        return issues
    
    def analyze_parameter_inconsistencies(self, code: str) -> List[CodeIssue]:
        """Detect inconsistent parameter usage"""
        issues = []
        
        # Look for targetVolume assignments
        target_volume_pattern = r'targetVolume\s*=\s*(\d+\.?\d*)'
        volume_matches = re.findall(target_volume_pattern, code)
        
        if len(set(volume_matches)) > 1:  # Different values found
            lines = code.split('\n')
            volume_lines = []
            
            for i, line in enumerate(lines, 1):
                if re.search(target_volume_pattern, line):
                    volume_lines.append((i, line.strip()))
            
            snippet_lines = ["# INCONSISTENT PARAMETERS:"]
            snippet_lines.append("")
            for line_num, line_content in volume_lines:
                snippet_lines.append(f"# Line {line_num}:")
                snippet_lines.append(line_content)
            
            unique_values = set(volume_matches)
            issue = CodeIssue(
                issue_type="Parameter Inconsistency",
                severity="medium",
                description=f"targetVolume has different values: {', '.join(unique_values)}",
                code_snippet='\n'.join(snippet_lines),
                suggestions=[
                    "Use consistent parameter values throughout the code",
                    "Define parameters as constants at the top of the file"
                ]
            )
            issues.append(issue)
        
        return issues
    
    def inspect_problematic_papers(self, output_dir: Path = Path("code_inspection")) -> Dict:
        """Inspect papers with known issues and generate human-readable reports"""
        output_dir.mkdir(exist_ok=True)
        
        # Load the summary to find problematic papers
        summary_file = Path("visualizations/summary_table.csv")
        if not summary_file.exists():
            print("❌ Run visualize_analysis_results.py first to generate summary")
            return {}
        
        try:
            import pandas as pd
            summary_df = pd.read_csv(summary_file)
        except ImportError:
            print("❌ pandas not available. Install with: pip install pandas")
            return {}
        
        # Find papers with issues
        problematic_papers = summary_df[
            (summary_df['has_mixed_apis'] == True) |
            (summary_df['syntax_error_rate'] > 0) |
            (summary_df['api_consistency'] < 0.8)
        ]
        
        print(f"🔍 Inspecting {len(problematic_papers)} papers with issues...")
        
        inspection_results = {}
        
        for _, paper_row in problematic_papers.iterrows():
            paper_id = paper_row['paper_id']
            paper_name = paper_row['paper_name']
            # Extract timestamp from paper_name (format: Name_TIMESTAMP)
            if '_2025' in paper_name:
                timestamp = paper_name.split('_')[-1]
            else:
                timestamp = "20250624_020624"  # default timestamp
            
            print(f"\n📋 Analyzing Paper {paper_id:02d}: {paper_name}")
            
            # Find corresponding JSON file
            json_pattern = f"paper_{paper_id:02d}_{paper_name}_{timestamp}_object_analysis.json"
            json_files = list(self.results_dir.glob(json_pattern))
            
            if not json_files:
                print(f"  ❌ JSON file not found: {json_pattern}")
                continue
            
            json_file = json_files[0]
            
            # Load the run info to find runs with issues
            with open(json_file, 'r') as f:
                analysis_data = json.load(f)
            
            run_info = analysis_data.get('run_info', [])
            paper_issues = []
            
            # Inspect each run
            for run_data in run_info:
                run_num = run_data['run']
                
                # Find the actual experiment data file
                exp_dir = Path("experiments") / f"paper_{paper_id:02d}_{paper_name}_{timestamp}"
                run_dir = exp_dir / f"run_{run_num}"
                exp_data_file = run_dir / "experiment_data.json"
                
                if not exp_data_file.exists():
                    continue
                
                try:
                    code_content, metadata = self.extract_code_from_json(exp_data_file)
                    if not code_content:
                        continue
                    
                    print(f"  🔍 Inspecting Run {run_num}...")
                    
                    # Analyze different types of issues
                    run_issues = []
                    run_issues.extend(self.analyze_api_mixing(code_content))
                    run_issues.extend(self.analyze_syntax_errors(code_content))
                    run_issues.extend(self.analyze_inconsistent_imports(code_content))
                    run_issues.extend(self.analyze_parameter_inconsistencies(code_content))
                    
                    if run_issues:
                        paper_issues.extend([(run_num, issue) for issue in run_issues])
                        print(f"    ✅ Found {len(run_issues)} issues")
                    else:
                        print(f"    ✅ No specific issues detected")
                
                except Exception as e:
                    print(f"    ❌ Error analyzing run {run_num}: {e}")
            
            # Generate report for this paper
            if paper_issues:
                self.generate_paper_report(paper_id, paper_name, paper_issues, output_dir)
                inspection_results[f"paper_{paper_id:02d}"] = paper_issues
        
        # Generate overall summary
        self.generate_overall_summary(inspection_results, output_dir)
        
        return inspection_results
    
    def generate_paper_report(self, paper_id: int, paper_name: str, issues: List[Tuple[int, CodeIssue]], output_dir: Path):
        """Generate a detailed report for a specific paper"""
        
        report_file = output_dir / f"paper_{paper_id:02d}_{paper_name}_issues.txt"
        
        report_content = f"""CODE INSPECTION REPORT
Paper {paper_id:02d}: {paper_name}
{'='*60}

SUMMARY:
- Total Issues Found: {len(issues)}
- Runs with Issues: {len(set(run_num for run_num, _ in issues))}

DETAILED ISSUES:
{'='*60}

"""
        
        # Group issues by run
        runs_with_issues = {}
        for run_num, issue in issues:
            if run_num not in runs_with_issues:
                runs_with_issues[run_num] = []
            runs_with_issues[run_num].append(issue)
        
        for run_num in sorted(runs_with_issues.keys()):
            run_issues = runs_with_issues[run_num]
            
            report_content += f"RUN {run_num}:\n"
            report_content += "-" * 20 + "\n\n"
            
            for i, issue in enumerate(run_issues, 1):
                report_content += f"Issue #{i}: {issue.issue_type} ({issue.severity.upper()} SEVERITY)\n"
                report_content += f"Description: {issue.description}\n\n"
                
                report_content += "PROBLEMATIC CODE:\n"
                report_content += "```python\n"
                report_content += issue.code_snippet
                report_content += "\n```\n\n"
                
                if issue.suggestions:
                    report_content += "SUGGESTIONS:\n"
                    for suggestion in issue.suggestions:
                        report_content += f"• {suggestion}\n"
                
                report_content += "\n" + "="*40 + "\n\n"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"  📝 Report saved: {report_file}")
    
    def generate_overall_summary(self, inspection_results: Dict, output_dir: Path):
        """Generate an overall summary of all issues found"""
        
        summary_file = output_dir / "overall_issues_summary.txt"
        
        # Count issues by type and severity
        issue_counts = {}
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        
        total_issues = 0
        
        for paper_key, paper_issues in inspection_results.items():
            for run_num, issue in paper_issues:
                issue_type = issue.issue_type
                severity = issue.severity
                
                if issue_type not in issue_counts:
                    issue_counts[issue_type] = 0
                issue_counts[issue_type] += 1
                severity_counts[severity] += 1
                total_issues += 1
        
        summary_content = f"""CODE INSPECTION OVERALL SUMMARY
{'='*50}

STATISTICS:
- Papers Inspected: {len(inspection_results)}
- Total Issues Found: {total_issues}

ISSUE BREAKDOWN BY TYPE:
"""
        
        for issue_type, count in sorted(issue_counts.items()):
            percentage = (count / total_issues * 100) if total_issues > 0 else 0
            summary_content += f"• {issue_type}: {count} ({percentage:.1f}%)\n"
        
        summary_content += f"""
ISSUE BREAKDOWN BY SEVERITY:
• High Severity: {severity_counts['high']} ({severity_counts['high']/total_issues*100:.1f}%)
• Medium Severity: {severity_counts['medium']} ({severity_counts['medium']/total_issues*100:.1f}%)
• Low Severity: {severity_counts['low']} ({severity_counts['low']/total_issues*100:.1f}%)

MOST COMMON ISSUES:
"""
        
        # Sort issues by frequency
        sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
        for issue_type, count in sorted_issues[:5]:
            summary_content += f"1. {issue_type}: {count} occurrences\n"
        
        summary_content += f"""

RECOMMENDATIONS:
• Focus on fixing High Severity issues first
• Mixed API issues are critical - they prevent code from running
• Syntax errors should be caught by better validation
• Consider using more consistent prompting to reduce variability

Check individual paper reports for detailed code examples and fixes.
"""
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_content)
        
        print(f"\n📊 Overall summary saved: {summary_file}")
        print(f"\n{summary_content}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Inspect problematic code and generate human-readable reports")
    parser.add_argument("--results-dir", "-r", type=str, default="analysis_results",
                       help="Directory containing analysis results")
    parser.add_argument("--output-dir", "-o", type=str, default="code_inspection",
                       help="Output directory for inspection reports")
    
    args = parser.parse_args()
    
    try:
        inspector = CodeInspector(Path(args.results_dir))
        results = inspector.inspect_problematic_papers(Path(args.output_dir))
        
        print(f"\n✅ Code inspection complete!")
        print(f"📁 Reports saved in: {args.output_dir}")
        print(f"🔍 Inspected {len(results)} papers with issues")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())