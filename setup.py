import setuptools

with open('./README.md', 'r') as readme_file:
    readme = readme_file.read()

with open('./tools/cl/runtime/package_requirements.txt') as package_requirements:
    install_requires = [line.strip() for line in package_requirements.readlines()]

setuptools.setup(
    name='cl-runtime',
    version='2.0.4',
    author='The Project Contributors',
    description='CompatibL Runtime Community Edition',
    license='Apache Software License',
    long_description=readme,
    long_description_content_type='text/markdown',
    install_requires=install_requires,
    url='https://github.com/compatibl/runtime',
    project_urls={
        'Repository': 'https://github.com/compatibl/runtime',
    },
    packages=setuptools.find_namespace_packages(
        where='.', include=['cl.runtime', 'cl.runtime.*', 'data'], exclude=['tests', 'tests.*']
    ),
    package_dir={'': '.'},
    package_data={
        '': ['py.typed'],
        'data': ['csv/**/*.csv', 'yaml/**/*.yaml', 'json/**/*.json'],
    },
    include_package_data=True,
    classifiers=[
        # Alpha - will attempt to avoid breaking changes but they remain possible
        'Development Status :: 3 - Alpha',

        # Audience and topic
        'Intended Audience :: Developers',
        'Topic :: Software Development',
        'Topic :: Scientific/Engineering',

        # License
        'License :: OSI Approved :: Apache Software License',

        # Runs on Python 3.10 and later releases
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',

        # Operating system
        'Operating System :: OS Independent',
    ],
)
