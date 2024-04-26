from distutils.core import setup

setup(  name='alphaSwc',
        version='1.0',
        description='Alpha wrapping of neurons from swc files',
        author ='Alex McSweeney-Davis',
        author_email='alex@mcsweeney-davis.com',
        url='https://github.com/alexmcsd/alphaSwc',
        packages=['alphaSwc'],
        python_requires='>=3.8',
        install_requires=[
        'numpy',
        'scipy',
        'trimesh',
        'pymeshlab>=2023.12.post1',
        ],
        include_package_data=True,

        classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Science/Research',
        'Intended Audience :: Developers',
        'Topic :: Scientific/Engineering :: Physics',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        ],
        keywords='diffusion mri, simulation, meshes, neuron reconstructions',
        project_urls={
        'Source': 'https://github.com/alexmcsd/alphaSwc',
        'Tracker': 'https://github.com/alexmcsd/alphaSwc/issues',
        },
        
        )