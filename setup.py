from setuptools import find_packages, setup

setup(
    name='ix-hapticsight-ohip',
    version='0.1.0',
    description='Safety-first optical-haptic interaction protocol reference implementation.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    author='Bryce Lovell',
    license='Apache-2.0',
    python_requires='>=3.10',
    package_dir={'': 'src'},
    packages=find_packages(where='src'),
    install_requires=['pyyaml>=6.0'],
    extras_require={'dev': ['pytest>=7.0']},
    keywords=[
        'robotics',
        'human-robot-interaction',
        'haptics',
        'safety',
        'consent',
        'protocol',
    ],
)
