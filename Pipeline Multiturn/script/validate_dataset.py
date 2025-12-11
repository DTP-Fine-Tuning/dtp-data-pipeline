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
    
    # Area Fungsi yang valid beserta range level
    AREA_FUNGSI_RANGES = {
        "Tata Kelola Teknologi Informasi": (3, 9),
        "Pengembangan Produk Digital": (2, 9),
        "Sains Data-Kecerdasan Artifisial": (2, 9),
        "Keamanan Informasi Dan Siber": (3, 9),
        "Teknologi Dan Infrastruktur": (2, 9),
        "Layanan Teknologi Informasi": (1, 8)
    }
    
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
            'area_mismatch_errors': 0,
            'level_range_errors': 0,
            'reasoning_inconsistency_errors': 0,
        }
        
        self.system_prompt = (
            "Anda adalah interviewer dari platform talenta digital Diploy khusus Area Fungsi. "
            "Tugas Anda adalah menggali detail kompetensi talenta berdasarkan data awal yang diberikan, "
            "meluruskan jawaban yang kurang relevan, dan memastikan informasi yang terkumpul cukup tajam "
            "untuk pemetaan Area Fungsi dan Level Okupasi. Gunakan bahasa Indonesia yang baik dan benar, "
            "tetap profesional, dan jangan menggunakan bahasa gaul atau singkatan informal."
        )
    
    def _parse_folder_name(self, filepath: Path) -> Tuple[Optional[str], Optional[int]]:
        """Parse area fungsi dan level dari nama folder.
        
        Format: Keamanan_Informasi_dan_Siber_3 -> ("Keamanan Informasi Dan Siber", 3)
        """
        try:
            # Get parent folder name
            folder_name = filepath.parent.name
            
            # Split by underscore
            parts = folder_name.split('_')
            
            if len(parts) < 2:
                return None, None
            
            # Last part should be level
            try:
                level = int(parts[-1])
            except ValueError:
                return None, None
            
            # Join other parts as area fungsi, replace _ with space and title case
            area_parts = parts[:-1]
            area_fungsi = ' '.join(area_parts)
            
            # Normalize: capitalize each word properly
            # Handle special cases: "dan", "Dan" -> "Dan"
            words = area_fungsi.split()
            normalized_words = []
            for word in words:
                if word.lower() == 'dan':
                    normalized_words.append('Dan')
                else:
                    normalized_words.append(word.capitalize())
            
            area_fungsi = ' '.join(normalized_words)
            
            return area_fungsi, level
            
        except Exception:
            return None, None
    
    def _normalize_area_fungsi(self, area: str) -> str:
        """Normalize area fungsi untuk comparison.
        
        Menangani variasi:
        - "Sains Data-Kecerdasan Artifisial" 
        - "Sains Data Kecerdasan Artifisial"
        - "sains data kecerdasan artifisial"
        Semua akan dinormalisasi menjadi bentuk yang sama.
        """
        if not area:
            return ""
        # Lowercase, remove extra spaces, replace hyphens with spaces
        normalized = ' '.join(area.split()).lower()
        # Replace hyphen with space untuk konsistensi
        normalized = normalized.replace('-', ' ')
        # Remove double spaces that might result
        normalized = ' '.join(normalized.split())
        return normalized
    
    def _validate_area_and_level(self, area_fungsi: str, level: int) -> Tuple[bool, Optional[str]]:
        """Validasi area fungsi dan level terhadap AREA_FUNGSI_RANGES."""
        # Normalize untuk comparison
        normalized_input = self._normalize_area_fungsi(area_fungsi)
        
        # Check against valid areas
        for valid_area, (min_level, max_level) in self.AREA_FUNGSI_RANGES.items():
            normalized_valid = self._normalize_area_fungsi(valid_area)
            
            if normalized_input == normalized_valid:
                # Found matching area, check level range
                if min_level <= level <= max_level:
                    return True, None
                else:
                    return False, f"Level {level} di luar range untuk {valid_area} (valid: {min_level}-{max_level})"
        
        # Area not found
        return False, f"Area Fungsi '{area_fungsi}' tidak valid (bukan salah satu dari 6 area yang ditentukan)"
    
    def validate_conversation_structure(self, messages: List[Dict], line_num: int, filename: str) -> Tuple[bool, Optional[str]]:
        """
        Validasi struktur conversation secara mendalam.
        
        Returns:
            (is_valid, error_message)
        """
        # Check 1: Must be a list
        if not isinstance(messages, list):
            return False, f"Messages bukan list, tipe: {type(messages)}"
        
        # Check 2: Minimum 3 messages (system + user + assistant)
        if len(messages) < 3:
            return False, f"Conversation terlalu pendek: {len(messages)} messages (minimum 3)"
        
        # Check 3: First message must be system
        if messages[0].get('role') != 'system':
            return False, f"First message bukan system: {messages[0].get('role')}"
        
        # Check 4: System prompt validation (lenient - check key phrases)
        system_content = messages[0].get('content', '').strip()
        # Lenient check - hanya validasi kata kunci penting
        key_phrases = ["interviewer", "Diploy", "Area Fungsi"]
        if not all(phrase in system_content for phrase in key_phrases):
            return False, f"System prompt tidak mengandung kata kunci yang diperlukan"
        
        # Check 5: Last message must be assistant
        if messages[-1].get('role') != 'assistant':
            return False, f"Last message bukan assistant: {messages[-1].get('role')}"
        
        # Check 6: Last assistant must contain [END OF CHAT] and <RESULT>
        last_content = messages[-1].get('content', '')
        if not last_content.strip().startswith('[END OF CHAT]'):
            return False, "Last assistant message harus diawali dengan '[END OF CHAT]'"
        
        if '<RESULT>' not in last_content or '</RESULT>' not in last_content:
            return False, "Last assistant message harus mengandung tag <RESULT>...</RESULT>"
        
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
        
        # Check 10: Extract and validate RESULT tag data
        import re
        result_match = re.search(r'<RESULT>(.*?)</RESULT>', last_content, re.DOTALL)
        if result_match:
            try:
                result_json = result_match.group(1).strip()
                result_data = json.loads(result_json)
                
                # Check for typos in field names
                if 'area_fungi' in result_data and 'area_fungsi' not in result_data:
                    return False, f"Typo dalam <RESULT>: 'area_fungi' seharusnya 'area_fungsi'"
                
                area_from_result = result_data.get('area_fungsi', '')
                level_from_result = result_data.get('level')
                
                # Reject if area_fungsi is unknown or empty
                if not area_from_result or area_from_result.lower() == 'unknown':
                    return False, f"Area Fungsi di <RESULT> tidak valid: '{area_from_result}' (harus berisi area fungsi yang valid)"
                
                # Reject if level is null or invalid
                if level_from_result is None:
                    return False, f"Level di <RESULT> tidak boleh null"
                
                # Validate area and level against AREA_FUNGSI_RANGES
                if area_from_result and level_from_result is not None:
                    try:
                        level_int = int(level_from_result)
                    except (ValueError, TypeError):
                        return False, f"Level di <RESULT> bukan integer valid: {level_from_result}"
                    
                    is_valid, error_msg = self._validate_area_and_level(area_from_result, level_int)
                    if not is_valid:
                        self.stats['level_range_errors'] += 1
                        return False, error_msg
                    
                    # Check 11: Validate against folder name (if available)
                    from pathlib import Path
                    if filename and filename != 'unknown':
                        filepath = Path(filename)
                        expected_area, expected_level = self._parse_folder_name(filepath)
                        
                        if expected_area and expected_level:
                            # Compare
                            if self._normalize_area_fungsi(area_from_result) != self._normalize_area_fungsi(expected_area):
                                self.stats['area_mismatch_errors'] += 1
                                return False, f"Area Fungsi di <RESULT> ({area_from_result}) tidak sesuai dengan folder ({expected_area})"
                            
                            if level_int != expected_level:
                                self.stats['area_mismatch_errors'] += 1
                                return False, f"Level di <RESULT> ({level_int}) tidak sesuai dengan folder ({expected_level})"
                    
                    # Check 12: Consistency between reasoning text and RESULT
                    # Extract area and level from reasoning text (before <RESULT> tag)
                    reasoning_text = last_content.split('<RESULT>')[0] if '<RESULT>' in last_content else last_content
                    
                    # Look for "Area Fungsi ... dan Level ..." with more precise regex
                    # Stop at "dan Level", "Level", or sentence end
                    reasoning_area_match = re.search(r'Area Fungsi[:\s]+([^.\n]+?)(?:\s+dan\s+Level|\s+Level)', reasoning_text, re.IGNORECASE)
                    reasoning_level_match = re.search(r'Level[:\s]+(\d+)', reasoning_text, re.IGNORECASE)
                    
                    if reasoning_area_match and reasoning_level_match:
                        reasoning_area = reasoning_area_match.group(1).strip()
                        # Clean up trailing "dan"
                        if reasoning_area.endswith(' dan'):
                            reasoning_area = reasoning_area[:-4].strip()
                        
                        reasoning_level = int(reasoning_level_match.group(1))
                        
                        # Compare with RESULT
                        if self._normalize_area_fungsi(reasoning_area) != self._normalize_area_fungsi(area_from_result):
                            self.stats['reasoning_inconsistency_errors'] += 1
                            return False, f"Inkonsistensi: reasoning menyebut '{reasoning_area}' tapi <RESULT> berisi '{area_from_result}'"
                        
                        if reasoning_level != level_int:
                            self.stats['reasoning_inconsistency_errors'] += 1
                            return False, f"Inkonsistensi: reasoning menyebut Level {reasoning_level} tapi <RESULT> berisi Level {level_int}"
                
            except json.JSONDecodeError as e:
                return False, f"<RESULT> tag berisi JSON tidak valid: {str(e)}"
            except Exception as e:
                return False, f"Error parsing <RESULT> tag: {str(e)}"
        
        return True, None
    
    def _validate_role_sequence(self, roles: List[str]) -> bool:
        """Validasi urutan role dalam conversation."""
        # System must be first
        if roles[0] != 'system':
            return False
        
        # Second message should be user
        if len(roles) > 1 and roles[1] != 'user':
            return False
        
        # After system, should be user or assistant
        for i in range(1, len(roles)):
            current = roles[i]
            previous = roles[i-1]
            
            # No consecutive system messages
            if current == 'system':
                return False
            
            # Allow alternating user/assistant pattern (lenient)
            # No strict enforcement, just catch obvious errors like consecutive users
            if current == previous and current == 'user':
                return False  # No consecutive user messages
        
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
            # Check for [END OF CHAT]
            if '[END OF CHAT]' in last_assistant_content:
                metadata['has_recommendation'] = True
            
            # Extract from <RESULT> tag
            import re
            result_match = re.search(r'<RESULT>(.*?)</RESULT>', last_assistant_content, re.DOTALL)
            if result_match:
                try:
                    result_data = json.loads(result_match.group(1))
                    metadata['area_fungsi'] = result_data.get('area_fungsi', None)
                    level_val = result_data.get('level', None)
                    if level_val is not None:
                        metadata['level'] = str(level_val)
                except json.JSONDecodeError:
                    pass
            
            # Fallback: Extract from text (only if RESULT parsing failed)
            if not metadata['area_fungsi']:
                # More precise regex: stop at "dan Level", "Level", period, or newline
                area_match = re.search(r'Area Fungsi[:\s]+([^.\n]+?)(?:\s+dan\s+Level|\s+Level|\.|\n)', last_assistant_content, re.IGNORECASE)
                if area_match:
                    area_text = area_match.group(1).strip()
                    # Additional cleanup: remove trailing "dan"
                    if area_text.endswith(' dan'):
                        area_text = area_text[:-4].strip()
                    metadata['area_fungsi'] = area_text
            
            if not metadata['level']:
                # Extract only the first Level number found
                level_match = re.search(r'Level[:\s]+(\d+)', last_assistant_content, re.IGNORECASE)
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
                        
                        # Deep validation (pass full filepath for folder name parsing)
                        is_valid, error_msg = self.validate_conversation_structure(
                            messages, line_num, str(filepath)
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
            print(f"   Area/Level mismatch with folder: {self.stats['area_mismatch_errors']}")
            print(f"   Level out of range: {self.stats['level_range_errors']}")
            print(f"   Reasoning inconsistency: {self.stats['reasoning_inconsistency_errors']}")
        
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
                for area, count in self.stats['area_distribution'].most_common(100):
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
                'area_mismatch': self.stats['area_mismatch_errors'],
                'level_range': self.stats['level_range_errors'],
                'reasoning_inconsistency': self.stats['reasoning_inconsistency_errors'],
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
