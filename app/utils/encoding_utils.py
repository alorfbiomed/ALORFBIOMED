"""
Encoding Detection and Handling Utilities

This module provides robust encoding detection and handling for file imports,
specifically designed to handle various text encodings commonly found in CSV files.
"""

import chardet
import codecs
import logging
from typing import Tuple, Optional, List, Union
from pathlib import Path
import io

from app.services.logging_service import LoggingService

logger = logging.getLogger(__name__)


class EncodingDetector:
    """Utility class for detecting and handling file encodings"""
    
    # Common encodings to try in order of preference
    COMMON_ENCODINGS = [
        'utf-8',
        'utf-8-sig',  # UTF-8 with BOM
        'windows-1252',  # Common Windows encoding
        'iso-8859-1',   # Latin-1
        'cp1252',       # Windows-1252 alias
        'latin1',       # ISO-8859-1 alias
        'ascii',
        'utf-16',
        'utf-16le',
        'utf-16be'
    ]
    
    @staticmethod
    def detect_file_encoding(file_path: Union[str, Path], sample_size: int = 100000) -> Tuple[str, float]:
        """
        Detect the encoding of a file using multiple methods
        
        Args:
            file_path: Path to the file to analyze
            sample_size: Number of bytes to read for detection (default: 100KB)
            
        Returns:
            Tuple of (encoding_name, confidence_score)
        """
        file_path = Path(file_path)
        
        try:
            # Read a sample of the file for detection
            with open(file_path, 'rb') as f:
                raw_data = f.read(sample_size)
            
            if not raw_data:
                LoggingService.log_warning(
                    "Empty file detected during encoding detection",
                    context={'file_path': str(file_path)},
                    logger_name='encoding'
                )
                return 'utf-8', 1.0
            
            # Use chardet for automatic detection
            detection_result = chardet.detect(raw_data)
            detected_encoding = detection_result.get('encoding', 'utf-8')
            confidence = detection_result.get('confidence', 0.0)
            
            LoggingService.log_info(
                f"Encoding detection completed: {detected_encoding}",
                context={
                    'file_path': str(file_path),
                    'detected_encoding': detected_encoding,
                    'confidence': confidence,
                    'sample_size': len(raw_data)
                },
                logger_name='encoding'
            )
            
            # Validate the detected encoding by trying to decode
            if detected_encoding and confidence > 0.7:
                try:
                    raw_data.decode(detected_encoding)
                    return detected_encoding, confidence
                except (UnicodeDecodeError, LookupError):
                    logger.warning(f"Detected encoding {detected_encoding} failed validation")
            
            # Fallback: try common encodings
            for encoding in EncodingDetector.COMMON_ENCODINGS:
                try:
                    raw_data.decode(encoding)
                    LoggingService.log_info(
                        f"Fallback encoding successful: {encoding}",
                        context={
                            'file_path': str(file_path),
                            'fallback_encoding': encoding,
                            'original_detection': detected_encoding
                        },
                        logger_name='encoding'
                    )
                    return encoding, 0.8  # Lower confidence for fallback
                except (UnicodeDecodeError, LookupError):
                    continue
            
            # Last resort: use utf-8 with error handling
            LoggingService.log_warning(
                "No suitable encoding found, defaulting to utf-8 with error handling",
                context={'file_path': str(file_path)},
                logger_name='encoding'
            )
            return 'utf-8', 0.5
            
        except Exception as e:
            LoggingService.log_error(
                "Error during encoding detection",
                exception=e,
                context={'file_path': str(file_path)},
                logger_name='encoding'
            )
            return 'utf-8', 0.0
    
    @staticmethod
    def read_file_with_encoding_detection(file_path: Union[str, Path], 
                                        fallback_encodings: List[str] = None) -> Tuple[str, str]:
        """
        Read a file with automatic encoding detection
        
        Args:
            file_path: Path to the file to read
            fallback_encodings: Additional encodings to try if detection fails
            
        Returns:
            Tuple of (file_content, used_encoding)
        """
        file_path = Path(file_path)
        
        if fallback_encodings is None:
            fallback_encodings = []
        
        # Detect encoding
        detected_encoding, confidence = EncodingDetector.detect_file_encoding(file_path)
        
        # Create list of encodings to try
        encodings_to_try = [detected_encoding] + fallback_encodings + EncodingDetector.COMMON_ENCODINGS
        # Remove duplicates while preserving order
        encodings_to_try = list(dict.fromkeys(encodings_to_try))
        
        for encoding in encodings_to_try:
            try:
                with open(file_path, 'r', encoding=encoding, errors='strict') as f:
                    content = f.read()
                
                LoggingService.log_info(
                    f"Successfully read file with encoding: {encoding}",
                    context={
                        'file_path': str(file_path),
                        'used_encoding': encoding,
                        'detected_encoding': detected_encoding,
                        'confidence': confidence,
                        'content_length': len(content)
                    },
                    logger_name='encoding'
                )
                
                return content, encoding
                
            except (UnicodeDecodeError, UnicodeError) as e:
                logger.debug(f"Failed to read file with encoding {encoding}: {str(e)}")
                continue
            except Exception as e:
                LoggingService.log_error(
                    f"Unexpected error reading file with encoding {encoding}",
                    exception=e,
                    context={'file_path': str(file_path), 'encoding': encoding},
                    logger_name='encoding'
                )
                continue
        
        # Last resort: read with utf-8 and replace errors
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            
            LoggingService.log_warning(
                "File read with UTF-8 and error replacement",
                context={
                    'file_path': str(file_path),
                    'used_encoding': 'utf-8 (with errors replaced)',
                    'content_length': len(content)
                },
                logger_name='encoding'
            )
            
            return content, 'utf-8'
            
        except Exception as e:
            LoggingService.log_error(
                "Failed to read file with any encoding method",
                exception=e,
                context={'file_path': str(file_path)},
                logger_name='encoding'
            )
            raise ValueError(f"Unable to read file {file_path} with any supported encoding") from e
    
    @staticmethod
    def convert_file_encoding(input_path: Union[str, Path], 
                            output_path: Union[str, Path], 
                            target_encoding: str = 'utf-8') -> bool:
        """
        Convert a file from its detected encoding to target encoding
        
        Args:
            input_path: Path to input file
            output_path: Path to output file
            target_encoding: Target encoding (default: utf-8)
            
        Returns:
            True if conversion successful, False otherwise
        """
        try:
            # Read file with encoding detection
            content, source_encoding = EncodingDetector.read_file_with_encoding_detection(input_path)
            
            # Write with target encoding
            with open(output_path, 'w', encoding=target_encoding, errors='replace') as f:
                f.write(content)
            
            LoggingService.log_info(
                f"File encoding conversion completed: {source_encoding} -> {target_encoding}",
                context={
                    'input_path': str(input_path),
                    'output_path': str(output_path),
                    'source_encoding': source_encoding,
                    'target_encoding': target_encoding,
                    'content_length': len(content)
                },
                logger_name='encoding'
            )
            
            return True
            
        except Exception as e:
            LoggingService.log_error(
                "File encoding conversion failed",
                exception=e,
                context={
                    'input_path': str(input_path),
                    'output_path': str(output_path),
                    'target_encoding': target_encoding
                },
                logger_name='encoding'
            )
            return False
    
    @staticmethod
    def create_text_stream_with_encoding_detection(file_stream, 
                                                 fallback_encodings: List[str] = None) -> Tuple[io.StringIO, str]:
        """
        Create a text stream from a binary file stream with encoding detection
        
        Args:
            file_stream: Binary file stream
            fallback_encodings: Additional encodings to try
            
        Returns:
            Tuple of (StringIO object, used_encoding)
        """
        if fallback_encodings is None:
            fallback_encodings = []
        
        # Read the binary data
        file_stream.seek(0)
        raw_data = file_stream.read()
        file_stream.seek(0)  # Reset for potential reuse
        
        if not raw_data:
            return io.StringIO(''), 'utf-8'
        
        # Detect encoding
        detection_result = chardet.detect(raw_data)
        detected_encoding = detection_result.get('encoding', 'utf-8')
        confidence = detection_result.get('confidence', 0.0)
        
        # Create list of encodings to try
        encodings_to_try = [detected_encoding] + fallback_encodings + EncodingDetector.COMMON_ENCODINGS
        encodings_to_try = list(dict.fromkeys(encodings_to_try))  # Remove duplicates
        
        for encoding in encodings_to_try:
            try:
                decoded_content = raw_data.decode(encoding)
                text_stream = io.StringIO(decoded_content)
                
                LoggingService.log_info(
                    f"Successfully created text stream with encoding: {encoding}",
                    context={
                        'used_encoding': encoding,
                        'detected_encoding': detected_encoding,
                        'confidence': confidence,
                        'content_length': len(decoded_content)
                    },
                    logger_name='encoding'
                )
                
                return text_stream, encoding
                
            except (UnicodeDecodeError, UnicodeError):
                continue
        
        # Last resort: decode with utf-8 and replace errors
        try:
            decoded_content = raw_data.decode('utf-8', errors='replace')
            text_stream = io.StringIO(decoded_content)
            
            LoggingService.log_warning(
                "Text stream created with UTF-8 and error replacement",
                context={
                    'used_encoding': 'utf-8 (with errors replaced)',
                    'detected_encoding': detected_encoding,
                    'content_length': len(decoded_content)
                },
                logger_name='encoding'
            )
            
            return text_stream, 'utf-8'
            
        except Exception as e:
            LoggingService.log_error(
                "Failed to create text stream with any encoding",
                exception=e,
                context={'detected_encoding': detected_encoding},
                logger_name='encoding'
            )
            raise ValueError("Unable to decode file stream with any supported encoding") from e
