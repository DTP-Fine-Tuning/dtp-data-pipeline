#!/usr/bin/env python3
"""
Dataset Multi-Turn Validator & Quality Analyzer

Script untuk validasi dan analisis kualitas dataset multi-turn conversation.
Mendeteksi:
- JSON corruption (JSON-in-string, escaped JSON)
- Format errors (missing fields, invalid roles)
- Structure issues (wrong sequence, empty content)
- Statistics & metrics

Usage:
    python validate_dataset.py /path/to/dataset/directory
    python validate_dataset.py /path/to/single/file.jsonl
    python validate_dataset.py --all  # validate semua output
"""

import json
import argparse
from pathlib import Path
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional
import sys
from datetime import datetime


class DatasetValidator:
    """Validator untuk dataset multi-turn conversation."""
    
    def __init__(self):
        self.stats = {
            'total_files': 0,
            'total_conversations': 0,
            'valid_conversations': 0,
            'invalid_conversations': 0,
            'errors_by_type': Counter(),
            'turn_distribution': Counter(),
            'mode_distribution': Counter(),
            'level_distribution': Counter(),
            'area_distribution': Counter(),
            'role_sequence_errors': 0,
            'json_corruption_errors': 0,
            'validation_errors': [],
        }
        
        self.system_prompt = (
            "Anda adalah interviewer dari platform talenta digital Diploy. "
            "Tugas Anda adalah menggali informasi pendidikan, pelatihan, sertifikasi, "
            "pengalaman kerja, dan keterampilan talenta sesuai data yang tersedia. "
            "Gunakan bahasa profesional & natural."
        )
    
    def validate_conversation_structure(self, messages: List[Dict], line_num: int, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validasi struktur conversation secara mendalam.
        
        Returns:
            (is_valid, error_message)
        """
        # Check 1: Must be a list
        if not isinstance(messages, list):
            return False, f"Messages bukan list, tipe: {type(messages)}"
        
        # Check 2: Minimum 2 messages
        if len(messages) < 2:
            return False, f"Conversation terlalu pendek: {len(messages)} messages"
        
        # Check 3: First message must be system
        if messages[0].get('role') != 'system':
            return False, f"First message bukan system: {messages[0].get('role')}"
        
        # Check 4: System prompt validation
        system_content = messages[0].get('content', '').strip()
        if system_content != self.system_prompt:
            return False, f"System prompt tidak sesuai (expected exact match)"
        
        # Check 5: Last message must be assistant
        if messages[-1].get('role') != 'assistant':
            return False, f"Last message bukan assistant: {messages[-1].get('role')}"
        
        # Check 6: Last assistant must contain recommendation
        last_content = messages[-1].get('content', '')
        if 'rekomendasi' not in last_content.lower() and 'recommendation' not in last_content.lower():
            return False, "Last assistant message tidak berisi rekomendasi"
        
        # Check 7: Detect JSON-in-string corruption
        for i, msg in enumerate(messages):
            content = msg.get('content', '')
            
            if not isinstance(content, str):
                return False, f"Message {i} content bukan string: {type(content)}"
            
            # Detect JSON corruption
            stripped = content.strip()
            if stripped.startswith('[{') or stripped.startswith('[\n  {'):
                self.stats['json_corruption_errors'] += 1
                return False, f"Message {i} ({msg.get('role')}) contains JSON array as string (CORRUPTION)"
            
            # Detect escaped JSON
            if '\\"role\\"' in content or '\\\"role\\\"' in content:
                self.stats['json_corruption_errors'] += 1
                return False, f"Message {i} ({msg.get('role')}) contains escaped JSON (CORRUPTION)"
        
        # Check 8: All messages must have role and content
        for i, msg in enumerate(messages):
            if 'role' not in msg:
                return False, f"Message {i} missing 'role' field"
            if 'content' not in msg:
                return False, f"Message {i} missing 'content' field"
            if msg['role'] not in ['system', 'user', 'assistant']:
                return False, f"Message {i} invalid role: {msg['role']}"
            if not msg['content'] or not msg['content'].strip():
                return False, f"Message {i} has empty content"
        
        # Check 9: Role sequence validation
        roles = [msg['role'] for msg in messages]
        if not self._validate_role_sequence(roles):
            self.stats['role_sequence_errors'] += 1
            return False, f"Invalid role sequence: {' -> '.join(roles)}"
        
        return True, None
    
    def _validate_role_sequence(self, roles: List[str]) -> bool:
        """Validasi urutan role dalam conversation."""
        # System must be first
        if roles[0] != 'system':
            return False
        
        # After system, should be user or assistant
        for i in range(1, len(roles)):
            current = roles[i]
            previous = roles[i-1]
            
            # No consecutive system messages
            if current == 'system':
                return False
            
            # Basic alternation check (not strict, but catch obvious errors)
            if current == previous and current != 'assistant':
                # Allow consecutive assistant (for multi-part responses)
                if not (current == 'assistant' and i == len(roles) - 1):
                    pass  # Lenient for now
        
        return True
    
    def extract_metadata(self, messages: List[Dict]) -> Dict:
        """Extract metadata dari conversation."""
        metadata = {
            'turn_count': len(messages),
            'mode': 'unknown',
            'area_fungsi': None,
            'level': None,
            'has_recommendation': False,
        }
        
        # Determine mode based on turn count
        turn_count = len(messages)
        if turn_count <= 3:
            metadata['mode'] = 'fast_direct'
        elif turn_count <= 4:
            metadata['mode'] = 'fast_short'
        elif turn_count <= 6:
            metadata['mode'] = 'medium'
        else:
            metadata['mode'] = 'long'
        
        # Extract recommendation info from last assistant message
        last_assistant_content = ''
        for msg in reversed(messages):
            if msg.get('role') == 'assistant':
                last_assistant_content = msg.get('content', '')
                break
        
        if last_assistant_content:
            content_lower = last_assistant_content.lower()
            if 'rekomendasi' in content_lower or 'recommendation' in content_lower:
                metadata['has_recommendation'] = True
            
            # Extract Area Fungsi
            import re
            area_match = re.search(r'Area Fungsi:\s*([^,.\n]+)', last_assistant_content, re.IGNORECASE)
            if area_match:
                metadata['area_fungsi'] = area_match.group(1).strip()
            
            # Extract Level
            level_match = re.search(r'Level:\s*(\d+|-)\.?', last_assistant_content, re.IGNORECASE)
            if level_match:
                metadata['level'] = level_match.group(1).strip()
        
        return metadata
    
    def validate_file(self, filepath: Path) -> Dict:
        """Validasi single JSONL file."""
        file_stats = {
            'filename': filepath.name,
            'filepath': str(filepath),
            'total_lines': 0,
            'valid_count': 0,
            'invalid_count': 0,
            'errors': [],
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    file_stats['total_lines'] += 1
                    self.stats['total_conversations'] += 1
                    
                    try:
                        # Parse JSON
                        data = json.loads(line)
                        
                        # Validate structure
                        if 'messages' not in data:
                            error_msg = "Missing 'messages' field"
                            file_stats['errors'].append({
                                'line': line_num,
                                'error': error_msg,
                                'severity': 'critical'
                            })
                            file_stats['invalid_count'] += 1
                            self.stats['invalid_conversations'] += 1
                            self.stats['errors_by_type']['missing_messages_field'] += 1
                            continue
                        
                        messages = data['messages']
                        
                        # Deep validation
                        is_valid, error_msg = self.validate_conversation_structure(
                            messages, line_num, filepath.name
                        )
                        
                        if not is_valid:
                            file_stats['errors'].append({
                                'line': line_num,
                                'error': error_msg,
                                'severity': 'critical'
                            })
                            file_stats['invalid_count'] += 1
                            self.stats['invalid_conversations'] += 1
                            
                            # Categorize error
                            if 'corruption' in error_msg.lower() or 'json' in error_msg.lower():
                                self.stats['errors_by_type']['json_corruption'] += 1
                            elif 'sequence' in error_msg.lower():
                                self.stats['errors_by_type']['role_sequence'] += 1
                            elif 'system' in error_msg.lower():
                                self.stats['errors_by_type']['system_prompt'] += 1
                            else:
                                self.stats['errors_by_type']['other'] += 1
                            
                            # Store detailed error
                            self.stats['validation_errors'].append({
                                'file': filepath.name,
                                'line': line_num,
                                'error': error_msg
                            })
                            
                            continue
                        
                        # Valid conversation - extract metadata
                        file_stats['valid_count'] += 1
                        self.stats['valid_conversations'] += 1
                        
                        metadata = self.extract_metadata(messages)
                        self.stats['turn_distribution'][metadata['turn_count']] += 1
                        self.stats['mode_distribution'][metadata['mode']] += 1
                        
                        if metadata['level']:
                            self.stats['level_distribution'][metadata['level']] += 1
                        if metadata['area_fungsi']:
                            self.stats['area_distribution'][metadata['area_fungsi']] += 1
                        
                    except json.JSONDecodeError as e:
                        error_msg = f"JSON decode error: {str(e)}"
                        file_stats['errors'].append({
                            'line': line_num,
                            'error': error_msg,
                            'severity': 'critical'
                        })
                        file_stats['invalid_count'] += 1
                        self.stats['invalid_conversations'] += 1
                        self.stats['errors_by_type']['json_decode'] += 1
                    
                    except Exception as e:
                        error_msg = f"Unexpected error: {str(e)}"
                        file_stats['errors'].append({
                            'line': line_num,
                            'error': error_msg,
                            'severity': 'critical'
                        })
                        file_stats['invalid_count'] += 1
                        self.stats['invalid_conversations'] += 1
                        self.stats['errors_by_type']['unexpected'] += 1
        
        except FileNotFoundError:
            file_stats['errors'].append({
                'line': 0,
                'error': 'File not found',
                'severity': 'critical'
            })
        except Exception as e:
            file_stats['errors'].append({
                'line': 0,
                'error': f'File read error: {str(e)}',
                'severity': 'critical'
            })
        
        return file_stats
    
    def validate_directory(self, directory: Path) -> List[Dict]:
        """Validasi semua JSONL files dalam directory."""
        jsonl_files = list(directory.rglob("*.jsonl"))
        
        if not jsonl_files:
            print(f"[WARNING] No JSONL files found in {directory}")
            return []
        
        print(f"\n{'='*70}")
        print(f"VALIDATING DATASET")
        print(f"{'='*70}")
        print(f"Directory: {directory}")
        print(f"Found: {len(jsonl_files)} JSONL files")
        print(f"{'='*70}\n")
        
        file_results = []
        self.stats['total_files'] = len(jsonl_files)
        
        for i, filepath in enumerate(jsonl_files, 1):
            print(f"[{i}/{len(jsonl_files)}] Validating: {filepath.name}...", end=' ')
            
            file_stats = self.validate_file(filepath)
            file_results.append(file_stats)
            
            if file_stats['invalid_count'] == 0:
                print(f"[SUCCESS] {file_stats['valid_count']} valid")
            else:
                print(f"[SUCCESS] {file_stats['valid_count']} valid, {file_stats['invalid_count']} invalid")
        
        return file_results
    
    def print_summary(self, file_results: List[Dict]):
        """Print comprehensive validation summary."""
        print(f"\n{'='*70}")
        print(f"[INFO] VALIDATION SUMMARY")
        print(f"{'='*70}")
        
        # Overall statistics
        print(f"\nFiles:")
        print(f"   Total files: {self.stats['total_files']}")
        print(f"   Files with errors: {sum(1 for f in file_results if f['invalid_count'] > 0)}")
        print(f"   Clean files: {sum(1 for f in file_results if f['invalid_count'] == 0)}")
        
        print(f"\nConversations:")
        print(f"   Total: {self.stats['total_conversations']}")
        print(f"   Valid: {self.stats['valid_conversations']} ({self.stats['valid_conversations']/max(self.stats['total_conversations'],1)*100:.1f}%)")
        print(f"   Invalid: {self.stats['invalid_conversations']} ({self.stats['invalid_conversations']/max(self.stats['total_conversations'],1)*100:.1f}%)")
        
        # Error breakdown
        if self.stats['invalid_conversations'] > 0:
            print(f"\n[FAILED] Errors by Type:")
            for error_type, count in self.stats['errors_by_type'].most_common():
                print(f"   {error_type}: {count} ({count/self.stats['invalid_conversations']*100:.1f}%)")
            
            print(f"\n[FAILED] Critical Errors:")
            print(f"   JSON corruption: {self.stats['json_corruption_errors']}")
            print(f"   Role sequence errors: {self.stats['role_sequence_errors']}")
        
        # Distribution statistics
        if self.stats['valid_conversations'] > 0:
            print(f"\nTurn Distribution:")
            for turn_count in sorted(self.stats['turn_distribution'].keys()):
                count = self.stats['turn_distribution'][turn_count]
                print(f"   {turn_count} turns: {count} ({count/self.stats['valid_conversations']*100:.1f}%)")
            
            print(f"\nMode Distribution:")
            for mode in ['fast_direct', 'fast_short', 'medium', 'long']:
                count = self.stats['mode_distribution'][mode]
                if count > 0:
                    print(f"   {mode.upper()}: {count} ({count/self.stats['valid_conversations']*100:.1f}%)")
            
            print(f"\nLevel Distribution:")
            for level in sorted(self.stats['level_distribution'].keys()):
                count = self.stats['level_distribution'][level]
                print(f"   Level {level}: {count} ({count/self.stats['valid_conversations']*100:.1f}%)")
            
            if self.stats['area_distribution']:
                print(f"\nTop 10 Area Fungsi:")
                for area, count in self.stats['area_distribution'].most_common(10):
                    print(f"   {area}: {count} ({count/self.stats['valid_conversations']*100:.1f}%)")
        
        # Files with errors
        if any(f['invalid_count'] > 0 for f in file_results):
            print(f"\nFILES WITH ERRORS:")
            for file_stat in file_results:
                if file_stat['invalid_count'] > 0:
                    print(f"\n {file_stat['filename']}")
                    print(f"Valid: {file_stat['valid_count']}, Invalid: {file_stat['invalid_count']}")
                    
                    # Show first 5 errors
                    for error in file_stat['errors'][:5]:
                        print(f"Line {error['line']}: {error['error']}")
                    
                    if len(file_stat['errors']) > 5:
                        print(f"... and {len(file_stat['errors']) - 5} more errors")
        
        # Quality score
        print(f"\n{'='*70}")
        if self.stats['total_conversations'] > 0:
            quality_score = (self.stats['valid_conversations'] / self.stats['total_conversations']) * 100
            
            if quality_score == 100:
                print(f"[SUCCESS] QUALITY SCORE: {quality_score:.1f}% - PERFECT!")
            elif quality_score >= 95:
                print(f"[SUCCESS] QUALITY SCORE: {quality_score:.1f}% - EXCELLENT")
            elif quality_score >= 90:
                print(f"[WARNING] QUALITY SCORE: {quality_score:.1f}% - GOOD")
            elif quality_score >= 80:
                print(f"[WARNING] QUALITY SCORE: {quality_score:.1f}% - FAIR")
            else:
                print(f"[BAD] QUALITY SCORE: {quality_score:.1f}% - NEEDS IMPROVEMENT")
        else:
            print(f"[FAILED] No conversations found!")
        
        print(f"{'='*70}\n")
    
    def export_report(self, output_path: Path, file_results: List[Dict]):
        """Export detailed validation report to JSON."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_files': self.stats['total_files'],
                'total_conversations': self.stats['total_conversations'],
                'valid_conversations': self.stats['valid_conversations'],
                'invalid_conversations': self.stats['invalid_conversations'],
                'quality_score': (self.stats['valid_conversations'] / max(self.stats['total_conversations'], 1)) * 100,
            },
            'errors': {
                'by_type': dict(self.stats['errors_by_type']),
                'json_corruption': self.stats['json_corruption_errors'],
                'role_sequence': self.stats['role_sequence_errors'],
            },
            'distributions': {
                'turns': dict(self.stats['turn_distribution']),
                'modes': dict(self.stats['mode_distribution']),
                'levels': dict(self.stats['level_distribution']),
                'areas': dict(self.stats['area_distribution']),
            },
            'file_details': file_results,
            'validation_errors': self.stats['validation_errors'][:100],  # Limit to 100
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"[INFO] Detailed report exported to: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate and analyze multi-turn conversation dataset',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python validate_dataset.py /path/to/dataset/directory
  python validate_dataset.py /path/to/file.jsonl
  python validate_dataset.py --all
  python validate_dataset.py /path/to/dataset --export report.json
        """
    )
    
    parser.add_argument(
        'path',
        nargs='?',
        help='Path to directory or JSONL file to validate'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Validate all datasets in MultiturnDatasetOutput directory'
    )
    parser.add_argument(
        '--export',
        type=str,
        metavar='FILE',
        help='Export detailed report to JSON file'
    )
    
    args = parser.parse_args()
    
    # Determine target path
    if args.all:
        # Default to MultiturnDatasetOutput
        script_dir = Path(__file__).parent
        target_path = script_dir.parent / "MultiturnDatasetOutput"
    elif args.path:
        target_path = Path(args.path)
    else:
        parser.print_help()
        sys.exit(1)
    
    if not target_path.exists():
        print(f"[FAILED] Error: Path not found: {target_path}")
        sys.exit(1)
    
    # Create validator
    validator = DatasetValidator()
    
    # Validate
    if target_path.is_file():
        print(f"Validating single file: {target_path}")
        file_results = [validator.validate_file(target_path)]
    else:
        file_results = validator.validate_directory(target_path)
    
    # Print summary
    validator.print_summary(file_results)
    
    # Export report if requested
    if args.export:
        export_path = Path(args.export)
        validator.export_report(export_path, file_results)
    
    # Exit with appropriate code
    if validator.stats['invalid_conversations'] > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
