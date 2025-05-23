from setuptools import setup
from os import path

current_folder = path.abspath(path.dirname(__file__))
long_description = open(path.join(current_folder, 'README.MD'), encoding='utf-8').read()

# https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/
setup(
    name="pizzoo",
    version="0.9.13",
    author="Pablo Huet",
    description="Pizzoo is a easy-to-use library for rendering on pixel matrix screens like the Pixoo64, featuring easy new device integration, animation tools, and XML template rendering support.",
    long_description=long_description,
	long_description_content_type='text/markdown',
	license="MIT AND (Apache-2.0 OR BSD-2-Clause)",
    keywords="pixoo, pixoo64, divoom, screen, pixel, matrix, render, buffer, LED matrix, LED, raspberry, raspberry pi",
    url="https://github.com/pabletos/pizzoo#readme",
	include_package_data=True,
    packages=['pizzoo'],
	package_dir={'pizzoo': 'pizzoo'},
	package_data={'pizzoo': ['*.bdf']},
    install_requires=[
        'requests ~= 2.31.0',
        'Pillow ~= 11.1.0',
		'bdfparser ~= 2.2.0'
    ],
	classifiers=[
        "Development Status :: 4 - Beta",
        "Topic :: Multimedia :: Graphics"
    ]
)