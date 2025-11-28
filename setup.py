from setuptools import setup, find_packages, Extension
from setuptools.command.build_ext import build_ext
import subprocess
import os
import sys
from pathlib import Path

class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)

class CMakeBuild(build_ext):
    def run(self):
        try:
            subprocess.check_output(['cmake', '--version'])
            has_cmake = True
        except OSError:
            print("??  CMake not found - installing Python-only version")
            print("   For better performance, install CMake and run: pip install --upgrade --force-reinstall isaac")
            has_cmake = False

        if has_cmake:
            try:
                for ext in self.extensions:
                    self.build_extension(ext)
                print("? C++ performance extensions built successfully")
            except Exception as e:
                print(f"??  C++ extension build failed: {e}")
                print("   Falling back to Python-only implementation")
                print("   Performance will be reduced but functionality preserved")
        else:
            print("?? Building Python-only version (C++ extensions not available)")

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        cmake_args = [
            '-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
            '-DPYTHON_EXECUTABLE=' + sys.executable,
            '-DCMAKE_BUILD_TYPE=Release'  # Always build in release mode for performance
        ]

        cfg = 'Release'  # Force release builds
        build_args = ['--config', cfg]

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        # Configure
        subprocess.check_call(['cmake', ext.sourcedir] + cmake_args,
                            cwd=self.build_temp)

        # Build with parallel jobs for faster compilation
        import multiprocessing
        build_args.extend(['--parallel', str(multiprocessing.cpu_count())])
        subprocess.check_call(['cmake', '--build', '.'] + build_args,
                            cwd=self.build_temp)

# Read requirements from requirements.txt
def read_requirements():
    """Read requirements from requirements.txt with error handling"""
    req_file = Path(__file__).parent / 'requirements.txt'
    if req_file.exists():
        with open(req_file, 'r') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    else:
        # Fallback to minimal requirements
        return [
            'requests>=2.31.0',
            'colorama>=0.4.6',
            'prompt-toolkit>=3.0.43',
            'pybind11>=2.10.0',
            'PyYAML>=6.0.1',
            'jsonschema>=4.20.0'
        ]

# Read long description from README
def read_long_description():
    """Read long description from README with fallback"""
    readme_files = ['README.md', 'readme.md', 'README.txt']
    for readme_file in readme_files:
        readme_path = Path(__file__).parent / readme_file
        if readme_path.exists():
            with open(readme_path, 'r', encoding='utf-8') as f:
                return f.read()
    return "Isaac - AI-Enhanced Command-Line Assistant"

# Check if C++ extensions should be built
def should_build_cpp():
    """Determine if C++ extensions should be built"""
    # Check for explicit disable
    if os.environ.get('ISAAC_NO_CPP', '').lower() in ('1', 'true', 'yes'):
        return False
    
    # Check if we're in CI/automated build (often problematic for C++)
    if os.environ.get('CI', '').lower() in ('1', 'true'):
        return False
    
    try:
        subprocess.check_output(['cmake', '--version'], stderr=subprocess.STDOUT)
        return True
    except:
        return False

# Determine extensions and command classes
if should_build_cpp():
    ext_modules = [CMakeExtension('isaac_core', sourcedir='src')]
    cmdclass = {'build_ext': CMakeBuild}
    print("??  C++ extensions will be built for optimal performance")
else:
    ext_modules = []
    cmdclass = {}
    print("?? Building Python-only version")

# Define optional dependency groups
extras_require = {
    'ai': [
        'openai>=2.7.1',
        'aiohttp>=3.13.2',
        'xai-sdk>=1.4.0',
    ],
    'performance': [
        'psutil>=7.1.3',
        'cython>=3.0.0',
    ],
    'dev': [
        'pytest>=9.0.0',
        'black>=25.9.0',
        'coverage>=7.11.2',
        'flake8-bugbear>=25.10.21',
    ],
    'full': [
        # AI dependencies
        'openai>=2.7.1',
        'aiohttp>=3.13.2',
        'xai-sdk>=1.4.0',
        # Performance dependencies  
        'psutil>=7.1.3',
        'cython>=3.0.0',
        # Additional features
        'pytesseract>=0.3.13',
        'matplotlib-inline>=0.2.1',
        'ttkbootstrap>=1.18.1',
    ]
}

setup(
    name='isaac',
    version='2.0.0',
    description='High-performance AI-enhanced shell assistant with hybrid C++/Python architecture',
    long_description=read_long_description(),
    long_description_content_type='text/markdown',
    author='Nick Demiduk',
    author_email='Nick.Demiduk@protonmail.com',
    url='https://github.com/cnc-n3r4/Isaac',
    packages=find_packages(),
    include_package_data=True,
    
    # Core requirements (always needed)
    install_requires=read_requirements(),
    
    # Optional dependencies
    extras_require=extras_require,
    
    # C++ extensions (if available)
    ext_modules=ext_modules,
    cmdclass=cmdclass,
    
    # Entry points
    entry_points={
        'console_scripts': [
            'isaac=isaac.__main__:main',
            'ask=isaac.commands.ask.run:main',
            'mine=isaac.commands.mine.run:main',
        ],
    },
    
    # Package data
    package_data={
        'isaac': [
            'data/*.json', 
            'data/*.txt',
            'data/*.yaml',
            'commands/*/command.yaml',
            'commands/*/run.py',
        ],
    },
    
    # Python version requirement
    python_requires='>=3.8',
    
    # PyPI classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Operating System :: OS Independent',
        'Topic :: System :: Shells',
        'Topic :: Software Development :: User Interfaces',
    ],
    
    keywords='shell assistant ai command-line productivity automation',
)