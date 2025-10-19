from setuptools import setup, find_packages

setup(
    name='isaac',
    version='2.0.0',
    description='Multi-platform intelligent shell assistant with cloud sync',
    author='Nick Demiduk',
    author_email='Nick.Demiduk@protonmail.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'requests>=2.31.0',
        'colorama>=0.4.6',
        'prompt-toolkit>=3.0.43',
    ],
    entry_points={
        'console_scripts': [
            'isaac=isaac.__main__:main',
        ],
    },
    package_data={
        'isaac': ['data/*.json', 'data/*.txt'],
    },
    python_requires='>=3.8',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
    ],
)