from isaac.dragdrop import BatchProcessor, BatchConfig
from pathlib import Path
import tempfile
import os

print('=== Testing Batch Processor ===')

# Create many test files (25 files to trigger batch processing)
test_files = []
for i in range(25):
    with tempfile.NamedTemporaryFile(mode='w', suffix=f'_test{i}.py', delete=False) as f:
        f.write(f'# Test file {i}\nprint("Hello from file {i}")')
        test_files.append(Path(f.name))

try:
    # Create batch processor with custom config
    config = BatchConfig(max_workers=2, batch_size=5)
    processor = BatchProcessor(config)

    print(f'Created batch processor with {config.max_workers} workers, batch size {config.batch_size}')

    # Create mock analysis (simplified)
    from isaac.dragdrop import BatchAnalysis, FileAnalysis, FileCategory

    analyses = []
    for i, path in enumerate(test_files):
        analysis = FileAnalysis(
            path=path,
            category=FileCategory.CODE,
            mime_type='text/x-python',
            size_bytes=len(f'# Test file {i}\nprint("Hello from file {i}")'),
            extension='.py',
            is_supported=True
        )
        analyses.append(analysis)

    batch_analysis = BatchAnalysis(
        files=analyses,
        total_size=sum(a.size_bytes for a in analyses),
        categories={FileCategory.CODE: len(analyses)},
        supported_count=len(analyses),
        unsupported_count=0,
        duplicates=[]
    )

    # Create decision to analyze code
    from isaac.dragdrop import DecisionResult, ActionType
    decision = DecisionResult(ActionType.ANALYZE_CODE, list(range(len(analyses))))

    print(f'Processing {len(analyses)} files with batch processor...')

    # Process the batch
    result = processor.process_batch(decision, batch_analysis)

    print(f'\nBatch processing result:')
    print(f'  Success: {result.success}')
    print(f'  Message: {result.message}')
    print(f'  Processed: {len(result.processed_files)}')
    print(f'  Failed: {len(result.failed_files)}')

    if result.output and 'analysis_results' in result.output:
        # Show analysis for first few files
        analysis_results = result.output['analysis_results']
        print(f'\nAnalysis results for first 3 files:')
        for i, (path_str, analysis_data) in enumerate(list(analysis_results.items())[:3]):
            path = Path(path_str)
            print(f'  {path.name}: {analysis_data.get("language", "unknown")}, {analysis_data.get("lines", 0)} lines')

finally:
    # Clean up
    for f in test_files:
        try:
            os.unlink(f)
        except:
            pass

print('\n=== Batch Processor Test Complete ===')