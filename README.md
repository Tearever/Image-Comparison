# Overview

This release introduces a standalone desktop application for comparing two images side by side, detecting visual differences, and highlighting them. The tool is designed for ease of use, supporting multiple file formats and offering both automatic and manual file selection.

Built using Python 3.13, Tkinter, OpenCV, Matplotlib, and scikit-image, this version focuses on simplicity, accuracy, and performance.

## New Features
 
## Image Comparison
- Supports PNG, JPG, JPEG, and WEBP images.
- Automatically detects and highlights pixel-level differences using SSIM (Structural Similarity Index).
- Displays original images and difference map side by side within the GUI.

## Difference Highlighting: 
- Draws bounding boxes around detected differences.
- Allows users to save a composite image showing highlighted regions.

## File Handling:
- Simplified file selection via menu or keyboard shortcuts (Ctrl+O, etc.).
- Automatically alternates between image slots for rapid comparison.

## Save & Export
- Option to export difference results as a single image.
- Automatically enables or disables save functionality depending on comparison results.

## Quality-of-Life Improvements
- Integrated logging/output area for real-time feedback.
- Responsive Tkinter layout with dynamic resizing support.
- Graceful handling of mismatched file types or dimensions.

## Technical Details
Language: Python 3.13.9
Core Libraries:
- opencv-python — for image processing and manipulation
- scikit-image — for SSIM comparison
- matplotlib — for visual output
- Pillow — for general image I/O
- tkinter — for GUI components

Executable Build Tool: auto-py-to-exe

# Known Limitations
- Images must currently be manually aligned if dimensions differ (future support for auto-resizing or alignment planned).
- Larger images may increase processing time.
