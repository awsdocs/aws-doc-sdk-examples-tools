#!/bin/bash
# Define paths
LAMBDA_DIR="lambda"  # Directory where your Lambda function code is
BUILD_DIR="build"    # Temporary directory to install dependencies
OUTPUT_ZIP="lambda_package.zip"  # Final zip package

# Clean up any previous builds
rm -rf $BUILD_DIR $OUTPUT_ZIP
mkdir -p $BUILD_DIR/python

# Install dependencies to the build directory
pip install -r $LAMBDA_DIR/requirements.txt -t $BUILD_DIR/python

# Copy Lambda code to the build directory
cp -r $LAMBDA_DIR/* $BUILD_DIR/python

# Zip everything in the build directory into the output zip
cd $BUILD_DIR/python && zip -r ../../$OUTPUT_ZIP . && cd ../../

# Clean up build directory
rm -rf $BUILD_DIR

